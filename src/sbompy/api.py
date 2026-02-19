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


app = FastAPI(title="SBOMPY", version=__version__, lifespan=lifespan)


@app.get("/health")
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
    "/sbom/run", response_model=JobResponse, dependencies=[Depends(require_api_key)]
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
)
def job_status(job_id: str):
    j = QUEUE.get_job(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="job not found")
    return JobResponse(
        job=j, results=j.get("results") if j["state"] in ("done", "failed") else None
    )


@app.get("/jobs", dependencies=[Depends(require_api_key)])
def jobs_recent(limit: int = 50):
    return {"jobs": QUEUE.list_recent(limit=limit)}


@app.get("/sbom/artifacts", dependencies=[Depends(require_api_key)])
def sbom_artifacts():
    return {"runs": list_runs(DATA_DIR)}


@app.get("/sbom/artifacts/{run_id}", dependencies=[Depends(require_api_key)])
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
)
async def stop_monitor(monitor_id: str) -> MonitorResponse:
    """Stop a running monitor."""
    try:
        m = await MONITORS.stop_monitor(monitor_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="monitor not found")
    return MonitorResponse.from_row(m)
