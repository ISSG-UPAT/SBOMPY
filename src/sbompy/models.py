"""
Pydantic models for SBOMPY's API surface.

SBOMPY focuses on:
- Discovering Docker containers/images on the host (via the Docker socket)
- Generating SBOMs via an external tool (syft or trivy)
- Persisting artifacts and job state for operational robustness
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

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


class DiscoverRequest(BaseModel):
    """Request payload for /sbom/discover."""

    filters: FilterSpec = Field(default_factory=FilterSpec)


class RunRequest(BaseModel):
    """
    Request payload for /sbom/run.

    If 'images' is provided, SBOMPY runs SBOM generation for those image references
    without container discovery (useful for testing or one-off scans).
    """

    tool: SbomTool = "syft"
    format: SbomFormat = "syft-json"
    timeout_s: int = Field(default=600, ge=10, le=7200)
    filters: FilterSpec = Field(default_factory=FilterSpec)
    images: Optional[List[str]] = Field(default=None)
    include_docker_info: bool = Field(default=False)


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
        default="if-not-present"
    )
    remove_volumes: bool = Field(default=True, description="Use `down -v`.")
    health_wait_seconds: int = Field(
        default=120,
        ge=0,
        description="Seconds to wait for containers to become healthy.",
    )


class JobOptions(BaseModel):
    """Options shared by static and deploy modes."""

    tool: SbomTool = "syft"
    format: SbomFormat = "syft-json"
    timeout_s: int = Field(default=600, ge=1, le=3600)
    include_docker_info: bool = False
    deploy: DeployOptions = Field(default_factory=DeployOptions)


class ImageJobInput(BaseModel):
    """Image input for v1 jobs."""

    type: Literal["image"] = "image"
    image_refs: List[str] = Field(min_length=1)


class ComposeJobInput(BaseModel):
    """Compose input for v1 jobs.

    Provide compose YAML content directly (best for API usage).
    File upload endpoints may store the compose file and pass a path instead.
    """

    type: Literal["compose"] = "compose"
    compose_yaml: str = Field(min_length=1)
    env: Dict[str, str] = Field(default_factory=dict)


JobInput = ImageJobInput | ComposeJobInput


class JobCreateRequest(BaseModel):
    """Create a v1 job."""

    mode: JobMode = "static"
    input: JobInput
    options: JobOptions = Field(default_factory=JobOptions)


# ---- monitor API (periodic scan) ----


class MonitorFilters(BaseModel):
    """Filters applied when scanning running containers."""

    labels: Dict[str, str] = Field(default_factory=dict)
    compose_project: Optional[str] = None
    namespace: Optional[str] = None
    namespace_label_key: str = "sbompy.namespace"
    require_label_key: Optional[str] = None
    require_label_value: Optional[str] = None


class MonitorOptions(BaseModel):
    """SBOM generation options for new images detected by the monitor."""

    tool: str = "syft"
    format: str = "syft-json"
    timeout_s: int = 600
    include_docker_info: bool = False


class MonitorCreateRequest(BaseModel):
    """Create a periodic monitor that scans for new running images."""

    interval_s: int = 60
    filters: MonitorFilters = Field(default_factory=MonitorFilters)
    options: MonitorOptions = Field(default_factory=MonitorOptions)


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
