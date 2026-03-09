"""
FastAPI application for SBOMPY.

Endpoints:
- GET  /health
- POST /sbom/discover
- POST /sbom/run
- GET  /jobs/{job_id}
- GET  /jobs               (recent jobs)
- GET  /sbom/artifacts
- GET  /sbom/artifacts/{run_id}

Production hardening:
- Optional API key auth via SBOMPY_API_KEY (X-API-Key header)
- Persistent jobs via sqlite
- Bounded worker concurrency via SBOMPY_WORKERS
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException

from .auth import require_api_key
from .docker_client import filter_containers, list_running_containers, resolve_images
from .jobs import JobQueue
from .monitor import MonitorManager
from .models import (
    DiscoverRequest,
    DiscoverResponse,
    JobCreateRequest,
    JobResponse,
    RunRequest,
    MonitorCreateRequest,
    MonitorResponse,
)
from .storage import list_runs, read_run_index
from ._version import __version__

DATA_DIR = Path("/data")
QUEUE = JobQueue(DATA_DIR)
MONITORS = MonitorManager(db=QUEUE.db, queue=QUEUE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "sboms").mkdir(exist_ok=True)
    (DATA_DIR / "cache").mkdir(exist_ok=True)
    await QUEUE.start()
    yield
    await QUEUE.stop()


app = FastAPI(
    title="SBOMPY",
    version=__version__,
    lifespan=lifespan,
    summary="API-triggered SBOM generation and monitoring for container images.",
    description=(
        "SBOMPY exposes a small REST API for discovering eligible workloads, "
        "starting SBOM generation jobs, polling job status, retrieving stored "
        "artifacts, and running periodic monitors that detect newly seen images.\n\n"
        "Authentication is controlled with the optional `SBOMPY_API_KEY` "
        "environment variable. When enabled, callers must provide the key in the "
        "`X-API-Key` header.\n\n"
        "The generated artifacts are persisted under `/data/sboms/<run_id>/` and "
        "can be consumed by external orchestration or assessment components."
    ),
    openapi_tags=[
        {
            "name": "system",
            "description": "Health and service availability endpoints.",
        },
        {
            "name": "sbom",
            "description": "Discovery and SBOM generation endpoints for running workloads or explicit image refs.",
        },
        {
            "name": "jobs",
            "description": "Asynchronous job creation and status inspection endpoints.",
        },
        {
            "name": "artifacts",
            "description": "Stored SBOM run metadata and artifact index endpoints.",
        },
        {
            "name": "monitors",
            "description": "Periodic background monitors that detect new images and trigger SBOM jobs.",
        },
    ],
)


@app.get(
    "/health",
    tags=["system"],
    summary="Health check",
    description="Simple readiness endpoint used to verify that the API process is running.",
)
def health():
    return {"ok": True}


def _filters_dict(f) -> dict:
    """
    Convert filters dataclass to dict for easier storage in job payload.
    Args:
        f: The filters dataclass instance.

    Returns:
        dict: The filters as a dictionary.
    """
    return {
        "labels": f.labels,
        "compose_project": f.compose_project,
        "namespace": f.namespace,
        "namespace_label_key": f.namespace_label_key,
        "require_label_key": f.require_label_key,
        "require_label_value": f.require_label_value,
    }


@app.post(
    "/sbom/discover",
    response_model=DiscoverResponse,
    dependencies=[Depends(require_api_key)],
    tags=["sbom"],
    summary="Discover eligible containers and images",
    description=(
        "Preview the running containers that match the provided filters and return "
        "their resolved image references, digests, and grouping information. This "
        "endpoint does not generate SBOMs; it helps callers confirm scope before "
        "starting a job."
    ),
)
def sbom_discover(req: DiscoverRequest):
    containers = list_running_containers()
    containers = filter_containers(
        containers,
        labels=req.filters.labels,
        compose_project=req.filters.compose_project,
        namespace=req.filters.namespace,
        namespace_label_key=req.filters.namespace_label_key,
        require_label_key=req.filters.require_label_key,
        require_label_value=req.filters.require_label_value,
    )
    container_map, images = resolve_images(containers)
    return DiscoverResponse(
        containers=container_map,
        images=images,
        matched_container_count=len(container_map),
    )


@app.post(
    "/sbom/run",
    response_model=JobResponse,
    dependencies=[Depends(require_api_key)],
    tags=["sbom"],
    summary="Create an SBOM generation job",
    description=(
        "Queue a background job that generates SBOM artifacts either for explicitly "
        "provided image refs or for images discovered from currently running "
        "containers that match the supplied filters."
    ),
)
async def sbom_run(req: RunRequest):
    job = QUEUE.create_job()
    filters = _filters_dict(req.filters)

    await QUEUE.enqueue(
        job["job_id"],
        payload={
            "tool": req.tool,
            "format": req.format,
            "timeout_s": req.timeout_s,
            "filters": filters,
            "images": req.images,
            "include_docker_info": req.include_docker_info,
        },
    )

    j = QUEUE.get_job(job["job_id"])
    return JobResponse(job=j, results=None)


@app.post(
    "/v1/jobs",
    response_model=JobResponse,
    dependencies=[Depends(require_api_key)],
    tags=["jobs"],
    summary="Create a v1 image or compose job",
    description=(
        "Create an asynchronous job using the newer v1 job format. The request can "
        "target a direct image list for static analysis or provide compose YAML for "
        "normalization and optional deploy-mode execution."
    ),
)
async def v1_create_job(req: JobCreateRequest):
    """Create a v1 job for static/deploy scanning of an image list or compose YAML."""
    job = QUEUE.create_job()
    await QUEUE.enqueue(
        job["job_id"],
        payload={
            "kind": "v1",
            "mode": req.mode,
            "input": req.input.model_dump(),
            "options": req.options.model_dump(),
        },
    )
    j = QUEUE.get_job(job["job_id"])
    return JobResponse(job=j, results=None)


@app.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    dependencies=[Depends(require_api_key)],
    tags=["jobs"],
    summary="Get job status",
    description=(
        "Return the current state of a queued, running, completed, or failed job. "
        "Completed and failed jobs include a results section with the persisted "
        "artifact index path when available."
    ),
)
def job_status(job_id: str):
    j = QUEUE.get_job(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="job not found")
    return JobResponse(
        job=j, results=j.get("results") if j["state"] in ("done", "failed") else None
    )


@app.get(
    "/jobs",
    dependencies=[Depends(require_api_key)],
    tags=["jobs"],
    summary="List recent jobs",
    description="Return recently created jobs ordered by recency.",
)
def jobs_recent(limit: int = 50):
    return {"jobs": QUEUE.list_recent(limit=limit)}


@app.get(
    "/sbom/artifacts",
    dependencies=[Depends(require_api_key)],
    tags=["artifacts"],
    summary="List stored SBOM runs",
    description=(
        "Return the available run identifiers under the persistent artifact "
        "directory. Each run id can be used to fetch the corresponding index."
    ),
)
def sbom_artifacts():
    return {"runs": list_runs(DATA_DIR)}


@app.get(
    "/sbom/artifacts/{run_id}",
    dependencies=[Depends(require_api_key)],
    tags=["artifacts"],
    summary="Get a stored SBOM run index",
    description=(
        "Read the persisted `index.json` for a specific run. The index contains "
        "run metadata, resolved images, summary counters, and per-image SBOM file paths."
    ),
)
def sbom_artifact_index(run_id: str):
    try:
        return read_run_index(DATA_DIR, run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="run_id not found")


# ---- monitors (periodic scanning) ----


@app.post(
    "/v1/monitors",
    response_model=MonitorResponse,
    dependencies=[Depends(require_api_key)],
    tags=["monitors"],
    summary="Create a periodic monitor",
    description=(
        "Start a background monitor that periodically scans running containers, "
        "tracks newly seen image digests, and triggers static SBOM jobs for newly "
        "detected images."
    ),
)
async def create_monitor(req: MonitorCreateRequest) -> MonitorResponse:
    """
    Start a periodic monitor that scans for newly running images and triggers SBOM jobs.

    The monitor triggers *static* SBOM generation jobs (v1 image jobs) for newly seen
    image digests.
    """
    m = await MONITORS.start_monitor(
        interval_s=req.interval_s,
        filters=req.filters.model_dump(),
        options=req.options.model_dump(),
    )
    return MonitorResponse.from_row(m)


@app.get(
    "/v1/monitors",
    dependencies=[Depends(require_api_key)],
    tags=["monitors"],
    summary="List monitors",
    description="Return recently created monitors and their current state.",
)
def list_monitors(limit: int = 50):
    """List recent monitors."""
    return {
        "monitors": [
            MonitorResponse.from_row(m).model_dump()
            for m in MONITORS.list_monitors(limit=limit)
        ]
    }


@app.get(
    "/v1/monitors/{monitor_id}",
    response_model=MonitorResponse,
    dependencies=[Depends(require_api_key)],
    tags=["monitors"],
    summary="Get monitor status",
    description="Return status and counters for a single monitor.",
)
def get_monitor(monitor_id: str) -> MonitorResponse:
    """Get a monitor by id."""
    m = MONITORS.get_monitor(monitor_id)
    if not m:
        raise HTTPException(status_code=404, detail="monitor not found")
    return MonitorResponse.from_row(m)


@app.post(
    "/v1/monitors/{monitor_id}/stop",
    response_model=MonitorResponse,
    dependencies=[Depends(require_api_key)],
    tags=["monitors"],
    summary="Stop a monitor",
    description="Stop a running periodic monitor and persist its final state.",
)
async def stop_monitor(monitor_id: str) -> MonitorResponse:
    """Stop a running monitor."""
    try:
        m = await MONITORS.stop_monitor(monitor_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="monitor not found")
    return MonitorResponse.from_row(m)
