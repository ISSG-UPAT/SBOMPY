"""
Pydantic models for SBOMPY's API surface.

SBOMPY focuses on:
- Discovering Docker containers/images on the host (via the Docker socket)
- Generating SBOMs via an external tool (syft or trivy)
- Persisting artifacts and job state for operational robustness
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict

SbomTool = Literal["syft", "trivy"]
SbomFormat = Literal[
    "cyclonedx-json",
    "spdx-json",
    "syft-json",
    "trivy-cyclonedx-json",
    "trivy-spdx-json",
]

JobState = Literal["queued", "running", "done", "failed"]


class FilterSpec(BaseModel):
    """
    Container selection filters.

    SBOMPY intentionally filters at the container layer (labels),
    because this is the most reliable way to target only "vertical" workloads.

    Typical usage in SAND5G:
      - sand5g.namespace=<vertical>
      - sand5g.managed=false
    """

    labels: Dict[str, str] = Field(
        default_factory=dict, description="Container labels to match (exact match)."
    )
    compose_project: Optional[str] = Field(
        default=None, description="Match docker-compose project name label."
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Match a namespace label value (e.g., a vertical name).",
    )
    namespace_label_key: str = Field(
        default="sand5g.namespace",
        description="Label key used for the namespace filter.",
    )

    # Hard allow-list: only containers that include this label/value are eligible.
    require_label_key: Optional[str] = Field(
        default=None,
        description="If set, containers must include this label (optionally with value).",
    )
    require_label_value: Optional[str] = Field(
        default=None,
        description="If require_label_key is set, enforce this value (exact). If null, only presence is required.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "labels": {"com.docker.compose.service": "web"},
                    "compose_project": "open5gs",
                    "namespace": "vertical-a",
                    "namespace_label_key": "sand5g.namespace",
                    "require_label_key": "sand5g.managed",
                    "require_label_value": "true",
                }
            ]
        }
    )


class DiscoverRequest(BaseModel):
    """Request payload for /sbom/discover."""

    filters: FilterSpec = Field(default_factory=FilterSpec)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "filters": {
                        "compose_project": "open5gs",
                        "namespace": "vertical-a",
                        "namespace_label_key": "sand5g.namespace",
                        "require_label_key": "sand5g.managed",
                        "require_label_value": "true",
                    }
                }
            ]
        }
    )


class RunRequest(BaseModel):
    """
    Request payload for /sbom/run.

    If 'images' is provided, SBOMPY runs SBOM generation for those image references
    without container discovery (useful for testing or one-off scans).
    """

    tool: SbomTool = Field(
        default="syft",
        description="SBOM backend used to generate artifacts for the selected images.",
    )
    format: SbomFormat = Field(
        default="syft-json",
        description="Output format produced by the selected SBOM backend.",
    )
    timeout_s: int = Field(
        default=600,
        ge=10,
        le=7200,
        description="Maximum time allowed for each SBOM generation operation.",
    )
    filters: FilterSpec = Field(
        default_factory=FilterSpec,
        description="Container filters used when `images` is omitted and SBOMPY must discover running workloads.",
    )
    images: Optional[List[str]] = Field(
        default=None,
        description="Optional explicit image refs to scan directly, bypassing container discovery.",
    )
    include_docker_info: bool = Field(
        default=False,
        description="Attach a sanitized subset of Docker daemon metadata to the stored run index.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tool": "syft",
                    "format": "syft-json",
                    "timeout_s": 600,
                    "filters": {
                        "namespace": "vertical-a",
                        "namespace_label_key": "sand5g.namespace",
                        "require_label_key": "sand5g.managed",
                        "require_label_value": "true",
                    },
                    "include_docker_info": False,
                },
                {
                    "tool": "syft",
                    "format": "syft-json",
                    "timeout_s": 600,
                    "images": ["ubuntu:20.04", "nginx:latest"],
                    "include_docker_info": True,
                },
            ]
        }
    )


class DiscoverImage(BaseModel):
    image_ref: str
    image_id: Optional[str] = None
    digest: Optional[str] = None
    containers: List[str] = Field(default_factory=list)


class DiscoverResponse(BaseModel):
    containers: Dict[str, Any]
    images: List[DiscoverImage]
    matched_container_count: int


class JobStatus(BaseModel):
    job_id: str
    state: JobState
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    output_dir: str
    run_id: Optional[str] = None
    error: Optional[str] = None
    summary: Dict[str, Any] = Field(default_factory=dict)


class JobResponse(BaseModel):
    job: JobStatus
    results: Optional[Dict[str, Any]] = None


# ---- v1 job API (image/compose static or deploy) ----

JobMode = Literal["static", "deploy"]
InputType = Literal["image", "compose"]


class DeployOptions(BaseModel):
    """Options controlling ephemeral docker compose deployment."""

    enabled: bool = Field(default=False, description="Enable deploy mode steps.")
    build: bool = Field(default=False, description="Allow docker compose build.")
    pull_policy: Literal["always", "if-not-present", "never"] = Field(
        default="if-not-present",
        description="Image pull behavior before SBOM generation in deploy mode.",
    )
    remove_volumes: bool = Field(default=True, description="Use `down -v`.")
    health_wait_seconds: int = Field(
        default=120,
        ge=0,
        description="Seconds to wait for containers to become healthy.",
    )


class JobOptions(BaseModel):
    """Options shared by static and deploy modes."""

    tool: SbomTool = Field(
        default="syft", description="SBOM backend used for the job."
    )
    format: SbomFormat = Field(
        default="syft-json", description="Artifact format produced by the job."
    )
    timeout_s: int = Field(
        default=600, ge=1, le=3600, description="Timeout applied to each scan step."
    )
    include_docker_info: bool = Field(
        default=False,
        description="Attach sanitized Docker daemon metadata to the generated run index.",
    )
    deploy: DeployOptions = Field(default_factory=DeployOptions)


class ImageJobInput(BaseModel):
    """Image input for v1 jobs."""

    type: Literal["image"] = "image"
    image_refs: List[str] = Field(
        min_length=1,
        description="One or more image refs, tags, or digests to scan.",
    )


class ComposeJobInput(BaseModel):
    """Compose input for v1 jobs.

    Provide compose YAML content directly (best for API usage).
    File upload endpoints may store the compose file and pass a path instead.
    """

    type: Literal["compose"] = "compose"
    compose_yaml: str = Field(
        min_length=1,
        description="Compose YAML content submitted inline for static or deploy-mode analysis.",
    )
    env: Dict[str, str] = Field(
        default_factory=dict,
        description="Optional environment variables used while normalizing the compose input.",
    )


JobInput = ImageJobInput | ComposeJobInput


class JobCreateRequest(BaseModel):
    """Create a v1 job."""

    mode: JobMode = Field(
        default="static",
        description="`static` scans existing image inputs, while `deploy` can perform a temporary compose deployment before scanning.",
    )
    input: JobInput
    options: JobOptions = Field(default_factory=JobOptions)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "mode": "static",
                    "input": {
                        "type": "image",
                        "image_refs": ["ubuntu:20.04", "ghcr.io/example/upf:1.0.0"],
                    },
                    "options": {
                        "tool": "syft",
                        "format": "syft-json",
                        "timeout_s": 600,
                        "include_docker_info": False,
                    },
                },
                {
                    "mode": "deploy",
                    "input": {
                        "type": "compose",
                        "compose_yaml": "services:\n  web:\n    image: nginx:latest\n",
                        "env": {"DEMO_ENV": "true"},
                    },
                    "options": {
                        "tool": "syft",
                        "format": "syft-json",
                        "timeout_s": 600,
                        "include_docker_info": True,
                        "deploy": {
                            "enabled": True,
                            "build": False,
                            "pull_policy": "if-not-present",
                            "remove_volumes": True,
                            "health_wait_seconds": 120,
                        },
                    },
                },
            ]
        }
    )


# ---- monitor API (periodic scan) ----


class MonitorFilters(BaseModel):
    """Filters applied when scanning running containers."""

    labels: Dict[str, str] = Field(
        default_factory=dict, description="Exact-match label filters."
    )
    compose_project: Optional[str] = Field(
        default=None, description="Restrict monitoring to a Docker Compose project."
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Restrict monitoring to a namespace label value, for example a vertical identifier.",
    )
    namespace_label_key: str = Field(
        default="sbompy.namespace",
        description="Label key used to interpret the namespace field during periodic scans.",
    )
    require_label_key: Optional[str] = Field(
        default=None,
        description="If set, only containers carrying this label are eligible.",
    )
    require_label_value: Optional[str] = Field(
        default=None,
        description="Optional value enforced for `require_label_key`.",
    )


class MonitorOptions(BaseModel):
    """SBOM generation options for new images detected by the monitor."""

    tool: str = Field(
        default="syft", description="SBOM backend used for triggered monitor jobs."
    )
    format: str = Field(
        default="syft-json", description="SBOM format used for triggered monitor jobs."
    )
    timeout_s: int = Field(
        default=600, description="Timeout used for each monitor-triggered scan."
    )
    include_docker_info: bool = Field(
        default=False,
        description="Attach sanitized Docker daemon metadata to triggered runs.",
    )


class MonitorCreateRequest(BaseModel):
    """Create a periodic monitor that scans for new running images."""

    interval_s: int = Field(
        default=60,
        description="Polling interval in seconds. Values below 5 are rounded up internally.",
    )
    filters: MonitorFilters = Field(default_factory=MonitorFilters)
    options: MonitorOptions = Field(default_factory=MonitorOptions)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "interval_s": 30,
                    "filters": {
                        "namespace": "vertical-a",
                        "namespace_label_key": "sand5g.namespace",
                        "require_label_key": "sand5g.managed",
                        "require_label_value": "true",
                    },
                    "options": {
                        "tool": "syft",
                        "format": "syft-json",
                        "timeout_s": 600,
                        "include_docker_info": False,
                    },
                }
            ]
        }
    )


class MonitorResponse(BaseModel):
    """Monitor state and metadata."""

    monitor_id: str
    state: str
    created_at: str
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    interval_s: int
    last_scan_at: Optional[str] = None
    error: Optional[str] = None
    triggered_jobs: int = 0
    seen_count: int = 0

    @classmethod
    def from_row(cls, m: Dict[str, Any]) -> "MonitorResponse":
        seen = (m.get("seen_json") or {}).get("digests") or []
        return cls(
            monitor_id=m["monitor_id"],
            state=m["state"],
            created_at=m["created_at"],
            started_at=m.get("started_at"),
            stopped_at=m.get("stopped_at"),
            interval_s=int(m.get("interval_s") or 60),
            last_scan_at=m.get("last_scan_at"),
            error=m.get("error"),
            triggered_jobs=int(m.get("triggered_jobs") or 0),
            seen_count=len(seen),
        )
