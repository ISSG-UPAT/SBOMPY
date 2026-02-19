"""
Job orchestration and background workers.

Production hardening features:
- Persistent job state via sqlite (/data/sbompy.sqlite)
- Worker queue with bounded concurrency (SBOMPY_WORKERS, default 2)
- Job recovery: on startup, queued/running jobs are marked failed (restart-safe)
- Output artifacts always written to /data/sboms/<run_id>/...

Note:
SBOMPY intentionally keeps the worker model simple and self-contained
(no external Redis/Celery dependency) for easy deployment inside SAND5G VMs.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .cache import read_cache, write_cache
from .db import JobDB
from .docker_client import (
    docker_info_safe,
    filter_containers,
    list_running_containers,
    resolve_images,
)
from .storage import make_run_dir, write_index, write_sbom_file
from .tools import generate_sbom


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_run_id(job_id: str) -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + job_id[:8]


def _safe_key(s: str) -> str:
    return s.replace("/", "_").replace(":", "_").replace("@", "_")


class JobQueue:
    """
    In-process job queue with background workers.

    Jobs are persisted in sqlite; the queue holds only job_ids and parameters.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.db = JobDB(base_dir / "sbompy.sqlite")
        self.q: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._running = False

    def create_job(self) -> Dict[str, Any]:
        job_id = uuid.uuid4().hex
        job = {
            "job_id": job_id,
            "state": "queued",
            "created_at": utcnow_iso(),
            "started_at": None,
            "finished_at": None,
            "output_dir": "",
            "run_id": None,
            "error": None,
            "summary": {},
            "results": None,
        }
        self.db.upsert_job(job)
        return job

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.db.get_job(job_id)

    def list_recent(self, limit: int = 50) -> list[Dict[str, Any]]:
        return self.db.list_recent(limit=limit)

    async def enqueue(self, job_id: str, payload: Dict[str, Any]) -> None:
        await self.q.put({"job_id": job_id, **payload})

    async def start(self) -> None:
        if self._running:
            return
        self._running = True

        # restart safety: queued/running jobs become failed
        reason = "Service restarted; previous job state was not resumable."
        self.db.mark_incomplete_as_failed(reason)

        workers = int(os.getenv("SBOMPY_WORKERS", "2"))
        workers = max(1, min(workers, 16))

        for i in range(workers):
            self._workers.append(asyncio.create_task(self._worker(i)))

    async def stop(self) -> None:
        self._running = False
        for t in self._workers:
            t.cancel()
        self._workers.clear()

    async def _worker(self, idx: int) -> None:
        while True:
            item = await self.q.get()
            try:
                await self._run_job(item)
            except Exception as e:
                job = self.db.get_job(item["job_id"])
                if job:
                    job["state"] = "failed"
                    job["finished_at"] = utcnow_iso()
                    job["error"] = str(e)
                    self.db.upsert_job(job)
            finally:
                self.q.task_done()

    async def _run_job(self, item: Dict[str, Any]) -> None:
        job_id = item["job_id"]
        job = self.db.get_job(job_id)
        if not job:
            return

        tool = item["tool"]
        fmt = item["format"]
        timeout_s = int(item["timeout_s"])
        filters = item.get("filters", {})
        images = item.get("images")
        include_docker_info = bool(item.get("include_docker_info", False))

        run_id = make_run_id(job_id)
        run_dir = make_run_dir(self.base_dir, run_id)

        job["state"] = "running"
        job["started_at"] = utcnow_iso()
        job["output_dir"] = str(run_dir)
        job["run_id"] = run_id
        self.db.upsert_job(job)

        # discovery
        if images:
            container_map: Dict[str, Any] = {}
            resolved_images = [
                {"image_ref": r, "digest": None, "image_id": None, "containers": []}
                for r in images
            ]
        else:
            containers = list_running_containers()
            containers = filter_containers(
                containers,
                labels=filters.get("labels", {}),
                compose_project=filters.get("compose_project"),
                namespace=filters.get("namespace"),
                namespace_label_key=filters.get(
                    "namespace_label_key", "sand5g.namespace"
                ),
                require_label_key=filters.get("require_label_key"),
                require_label_value=filters.get("require_label_value"),
            )
            container_map, resolved_images = resolve_images(containers)

        docker_info = docker_info_safe() if include_docker_info else None

        results: Dict[str, Any] = {}
        sbom_files: Dict[str, str] = {}
        cache_hits = 0
        ok_count = 0

        for img in resolved_images:
            image_ref = img["image_ref"]
            digest = img.get("digest")
            file_key = f"{_safe_key(digest or image_ref)}__{tool}__{fmt}"

            cached = read_cache(self.base_dir, digest, tool, fmt)
            if cached is not None:
                cache_hits += 1
                wrapper = {"ok": True, "cached": True, "sbom": cached}
            else:
                out = generate_sbom(
                    tool=tool, image_ref=image_ref, fmt=fmt, timeout_s=timeout_s
                )
                if out.get("ok"):
                    write_cache(self.base_dir, digest, tool, fmt, out["json"])
                    wrapper = {"ok": True, "cached": False, "sbom": out["json"]}
                else:
                    wrapper = {"ok": False, **out}

            if wrapper.get("ok"):
                ok_count += 1

            results[image_ref] = wrapper
            p = write_sbom_file(run_dir, file_key, wrapper)
            sbom_files[image_ref] = str(p)

        finished = utcnow_iso()
        index = {
            "run_id": run_id,
            "job_id": job_id,
            "created_at": job["created_at"],
            "started_at": job["started_at"],
            "finished_at": finished,
            "tool": tool,
            "format": fmt,
            "timeout_s": timeout_s,
            "filters": filters,
            "mode": "explicit" if images else "discovered",
            "containers": container_map,
            "images": resolved_images,
            "sbom_files": sbom_files,
            "docker_info": docker_info,
            "cache_hits": cache_hits,
            "ok_count": ok_count,
            "image_count": len(resolved_images),
        }
        write_index(run_dir, index)

        job["finished_at"] = finished
        if ok_count == len(resolved_images):
            job["state"] = "done"
        else:
            job["state"] = "failed"
            job["error"] = (
                "One or more SBOM generations failed. See index.json for details."
            )

        job["summary"] = {
            "run_id": run_id,
            "image_count": len(resolved_images),
            "ok_count": ok_count,
            "cache_hits": cache_hits,
        }
        job["results"] = {"index_path": str(run_dir / "index.json")}
        self.db.upsert_job(job)
