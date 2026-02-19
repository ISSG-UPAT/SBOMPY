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
