"""
Periodic monitoring of running Docker containers for new images.

This module implements a long-running "monitor" task that periodically scans
the Docker daemon for currently running containers, detects newly seen images,
and triggers SBOM generation jobs for those images.

Security note:
- This monitor performs *static* SBOM generation for images found on the host.
- It does not automatically deploy arbitrary workloads.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set, List

from .docker_client import list_running_containers, filter_containers, resolve_image_ref
from .db import JobDB


@dataclass(frozen=True)
class MonitorHandle:
    """In-memory handle for a running monitor task."""

    monitor_id: str
    task: asyncio.Task
    stop_event: asyncio.Event


class MonitorManager:
    """
    Manage periodic monitor tasks.

    Monitors are persisted in sqlite (monitors table) for auditability.
    Active monitor loops are kept in-memory; on restart, monitors are not
    automatically resumed (restart-safe by default).
    """

    def __init__(self, *, db: JobDB, queue: Any):
        self._db = db
        self._queue = queue
        self._handles: Dict[str, MonitorHandle] = {}

    def list_monitors(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._db.list_monitors(limit=limit)

    def get_monitor(self, monitor_id: str) -> Optional[Dict[str, Any]]:
        return self._db.get_monitor(monitor_id)

    async def start_monitor(
        self, *, interval_s: int, filters: Dict[str, Any], options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create and start a monitor."""
        interval_s = int(interval_s)
        if interval_s < 5:
            interval_s = 5

        monitor_id = uuid.uuid4().hex
        monitor = {
            "monitor_id": monitor_id,
            "state": "running",
            "created_at": self._queue.utcnow_iso(),
            "started_at": self._queue.utcnow_iso(),
            "stopped_at": None,
            "interval_s": interval_s,
            "last_scan_at": None,
            "error": None,
            "filters_json": filters,
            "options_json": options,
            "seen_json": {"digests": []},
            "triggered_jobs": 0,
        }
        self._db.upsert_monitor(monitor)

        stop_event = asyncio.Event()
        task = asyncio.create_task(self._run_loop(monitor_id, stop_event))
        self._handles[monitor_id] = MonitorHandle(
            monitor_id=monitor_id, task=task, stop_event=stop_event
        )
        return monitor

    async def stop_monitor(self, monitor_id: str) -> Dict[str, Any]:
        """Stop a running monitor."""
        h = self._handles.get(monitor_id)
        if h:
            h.stop_event.set()
            h.task.cancel()
            try:
                await h.task
            except Exception:
                pass
            self._handles.pop(monitor_id, None)

        m = self._db.get_monitor(monitor_id)
        if not m:
            raise KeyError(monitor_id)
        if m.get("state") != "stopped":
            m["state"] = "stopped"
            m["stopped_at"] = self._queue.utcnow_iso()
            self._db.upsert_monitor(m)
        return m

    def is_active(self, monitor_id: str) -> bool:
        return monitor_id in self._handles

    async def _run_loop(self, monitor_id: str, stop_event: asyncio.Event) -> None:
        while True:
            if stop_event.is_set():
                return
            try:
                await self._scan_once(monitor_id)
            except asyncio.CancelledError:
                return
            except Exception as e:
                m = self._db.get_monitor(monitor_id)
                if m:
                    m["error"] = str(e)
                    self._db.upsert_monitor(m)
            # wait
            m = self._db.get_monitor(monitor_id)
            interval_s = int((m or {}).get("interval_s", 60))
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval_s)
            except asyncio.TimeoutError:
                pass

    def _container_image_digest(self, c: Any) -> Optional[str]:
        """Best-effort: return sha256 digest for container image."""
        try:
            # docker SDK image attrs contain RepoDigests if available
            img = c.image
            repo_digests = (getattr(img, "attrs", {}) or {}).get("RepoDigests") or []
            if repo_digests:
                # format: name@sha256:...
                rd = repo_digests[0]
                if "@sha256:" in rd:
                    return "sha256:" + rd.split("@sha256:", 1)[1]
            # fallback to image id (already sha256:...)
            image_id = getattr(img, "id", None)
            if isinstance(image_id, str) and image_id.startswith("sha256:"):
                return image_id
        except Exception:
            return None
        return None

    async def _scan_once(self, monitor_id: str) -> None:
        m = self._db.get_monitor(monitor_id)
        if not m:
            return
        if m.get("state") != "running":
            return

        filters = m.get("filters_json") or {}
        options = m.get("options_json") or {}

        containers = list_running_containers()
        # apply same filter model used elsewhere
        f_labels = filters.get("labels") or {}
        compose_project = filters.get("compose_project")
        namespace = filters.get("namespace")
        namespace_label_key = filters.get("namespace_label_key", "sbompy.namespace")
        require_label_key = filters.get("require_label_key")
        require_label_value = filters.get("require_label_value")

        filtered = filter_containers(
            containers,
            labels=f_labels,
            compose_project=compose_project,
            namespace=namespace,
            namespace_label_key=namespace_label_key,
            require_label_key=require_label_key,
            require_label_value=require_label_value,
        )

        # load seen set
        seen_json = m.get("seen_json") or {"digests": []}
        seen: Set[str] = set(seen_json.get("digests") or [])

        new_digests: Set[str] = set()
        new_refs: List[str] = []
        for c in filtered:
            digest = self._container_image_digest(c)
            if digest and digest not in seen:
                new_digests.add(digest)
            # also track tags if present (optional convenience for SBOM tools)
            try:
                tags = getattr(c.image, "tags", None) or []
                if tags:
                    new_refs.append(tags[0])
            except Exception:
                pass

        if not new_digests:
            m["last_scan_at"] = self._queue.utcnow_iso()
            self._db.upsert_monitor(m)
            return

        # trigger SBOM jobs for new digests (prefer digests; fall back to refs)
        tool = options.get("tool") or "syft"
        fmt = options.get("format") or "syft-json"
        timeout_s = int(options.get("timeout_s", 600))
        include_docker_info = bool(options.get("include_docker_info", False))

        # create one job per digest for better auditability
        for digest in sorted(new_digests):
            job = self._queue.create_job()
            payload = {
                "kind": "v1",
                "mode": "static",
                "input": {"type": "image", "image_refs": [digest]},
                "options": {
                    "tool": tool,
                    "format": fmt,
                    "timeout_s": timeout_s,
                    "include_docker_info": include_docker_info,
                },
            }
            await self._queue.enqueue(job["job_id"], payload)
            m["triggered_jobs"] = int(m.get("triggered_jobs") or 0) + 1

        # update seen
        seen.update(new_digests)
        m["seen_json"] = {"digests": sorted(seen)}
        m["last_scan_at"] = self._queue.utcnow_iso()
        self._db.upsert_monitor(m)
