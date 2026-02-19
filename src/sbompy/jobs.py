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
from .compose import ComposeOrchestrator
from .inputs import InputNormalizer
from .policy import ComposePolicy
from .docker_client import (
    docker_info_safe,
    filter_containers,
    list_running_containers,
    resolve_images,
    resolve_image_ref,
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

    def utcnow_iso(self) -> str:
        """Return current UTC time in ISO 8601 format."""
        return utcnow_iso()

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

        kind = item.get("kind")
        if kind == "v1":
            await self._run_job_v1(item)
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

    async def _run_job_v1(self, item: Dict[str, Any]) -> None:
        """Run a v1 job created by /v1/jobs."""
        job_id = item["job_id"]
        job = self.db.get_job(job_id)
        if not job:
            return

        mode = item.get("mode", "static")
        input_obj = item.get("input") or {}
        options = item.get("options") or {}

        tool = options.get("tool", "syft")
        fmt = options.get("format", "syft-json")
        timeout_s = int(options.get("timeout_s", 600))
        include_docker_info = bool(options.get("include_docker_info", False))

        deploy_opts = options.get("deploy") or {}
        deploy_enabled = bool(deploy_opts.get("enabled", False))
        build = bool(deploy_opts.get("build", False))
        pull_policy = str(deploy_opts.get("pull_policy", "if-not-present"))
        remove_volumes = bool(deploy_opts.get("remove_volumes", True))
        health_wait_seconds = int(deploy_opts.get("health_wait_seconds", 120))

        run_id = make_run_id(job_id)
        run_dir = make_run_dir(self.base_dir, run_id)
        workspace = run_dir / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)

        job["state"] = "running"
        job["started_at"] = utcnow_iso()
        job["output_dir"] = str(run_dir)
        job["run_id"] = run_id
        job["error"] = None
        self.db.upsert_job(job)

        normalizer = InputNormalizer(workspace)
        normalized = None
        policy_violations = []

        if input_obj.get("type") == "image":
            image_refs = list(input_obj.get("image_refs") or [])
            normalized = normalizer.from_image_refs(image_refs)
        elif input_obj.get("type") == "compose":
            compose_yaml = str(input_obj.get("compose_yaml") or "")
            env = dict(input_obj.get("env") or {})
            normalized = normalizer.from_compose_yaml(compose_yaml, env=env)
            pol = ComposePolicy()
            if normalized.compose_file:
                policy_violations = [
                    v.__dict__ for v in pol.validate_file(normalized.compose_file)
                ]
        else:
            raise ValueError("Unsupported v1 input type")

        # If policy violations exist, do not allow deploy-mode execution.
        if policy_violations and mode == "deploy" and deploy_enabled:
            finished = utcnow_iso()
            job["state"] = "failed"
            job["finished_at"] = finished
            job["error"] = "Compose policy violations prevent deploy-mode execution."
            job["summary"] = {
                "run_id": run_id,
                "policy_violations": len(policy_violations),
            }
            job["results"] = {"index_path": str(run_dir / "index.json")}
            self.db.upsert_job(job)

            write_index(
                run_dir,
                {
                    "run_id": run_id,
                    "job_id": job_id,
                    "kind": "v1",
                    "mode": mode,
                    "deploy": {"enabled": deploy_enabled},
                    "input": normalized.__dict__ if normalized else {},
                    "policy_violations": policy_violations,
                },
            )
            return

        deploy_result = None
        if mode == "deploy" and deploy_enabled:
            if not normalized.compose_file:
                raise ValueError("deploy mode requires compose input")

            project = f"sbompy_{job_id[:8]}"
            orch = ComposeOrchestrator(
                compose_file=normalized.compose_file,
                project=project,
                workdir=normalized.compose_file.parent,
            )
            up_res = orch.up(build=build, pull_policy=pull_policy, timeout_s=timeout_s)
            ps_json = orch.ps_json(timeout_s=min(60, timeout_s))
            deploy_result = {
                "project": project,
                "services": up_res.services,
                "ps_json": ps_json,
                "health_wait_seconds": health_wait_seconds,
            }
            orch.down(remove_volumes=remove_volumes, timeout_s=timeout_s)

        resolved_images = []
        results: Dict[str, Any] = {}
        sbom_files: Dict[str, str] = {}
        cache_hits = 0
        ok_count = 0

        pull = bool(
            mode == "deploy"
            and deploy_enabled
            and pull_policy in ("always", "if-not-present")
        )

        for ref in normalized.image_refs:
            r = resolve_image_ref(ref, pull=pull)
            resolved_images.append(r)
            digest = r.get("digest")
            file_key = f"{_safe_key(digest or ref)}__{tool}__{fmt}"

            cached = read_cache(self.base_dir, digest, tool, fmt) if digest else None
            if cached is not None:
                cache_hits += 1
                wrapper = {"ok": True, "cached": True, "sbom": cached}
            else:
                out = generate_sbom(
                    tool=tool, image_ref=ref, fmt=fmt, timeout_s=timeout_s
                )
                if out.get("ok"):
                    if digest:
                        write_cache(self.base_dir, digest, tool, fmt, out["json"])
                    wrapper = {"ok": True, "cached": False, "sbom": out["json"]}
                else:
                    wrapper = {"ok": False, **out}

            if wrapper.get("ok"):
                ok_count += 1

            results[ref] = wrapper
            p = write_sbom_file(run_dir, file_key, wrapper)
            sbom_files[ref] = str(p)

        docker_info = docker_info_safe() if include_docker_info else None
        finished = utcnow_iso()

        index = {
            "run_id": run_id,
            "job_id": job_id,
            "created_at": job["created_at"],
            "started_at": job["started_at"],
            "finished_at": finished,
            "kind": "v1",
            "mode": mode,
            "deploy": {
                "enabled": deploy_enabled,
                "options": {
                    "build": build,
                    "pull_policy": pull_policy,
                    "remove_volumes": remove_volumes,
                    "health_wait_seconds": health_wait_seconds,
                },
                "result": deploy_result,
            },
            "tool": tool,
            "format": fmt,
            "timeout_s": timeout_s,
            "input": {
                "kind": normalized.kind if normalized else None,
                "input_hash": normalized.input_hash if normalized else None,
                "image_refs": normalized.image_refs if normalized else [],
                "compose_file": (
                    str(normalized.compose_file)
                    if (normalized and normalized.compose_file)
                    else None
                ),
            },
            "policy_violations": policy_violations,
            "images_resolved": resolved_images,
            "sbom_files": sbom_files,
            "docker_info": docker_info,
            "cache_hits": cache_hits,
            "ok_count": ok_count,
            "image_count": len(resolved_images),
        }
        write_index(run_dir, index)

        job["finished_at"] = finished
        job["state"] = "done" if ok_count == len(resolved_images) else "failed"
        if job["state"] != "done":
            job["error"] = (
                "One or more SBOM generations failed. See index.json for details."
            )

        job["summary"] = {
            "run_id": run_id,
            "image_count": len(resolved_images),
            "ok_count": ok_count,
            "cache_hits": cache_hits,
            "mode": mode,
        }
        job["results"] = {"index_path": str(run_dir / "index.json")}
        self.db.upsert_job(job)
