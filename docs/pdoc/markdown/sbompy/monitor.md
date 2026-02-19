Module sbompy.monitor
=====================
Periodic monitoring of running Docker containers for new images.

This module implements a long-running "monitor" task that periodically scans
the Docker daemon for currently running containers, detects newly seen images,
and triggers SBOM generation jobs for those images.

Security note:
- This monitor performs *static* SBOM generation for images found on the host.
- It does not automatically deploy arbitrary workloads.

Classes
-------

`MonitorHandle(monitor_id: str, task: asyncio.Task, stop_event: asyncio.Event)`
:   In-memory handle for a running monitor task.

    ### Instance variables

    `monitor_id: str`
    :   The type of the None singleton.

    `stop_event: asyncio.locks.Event`
    :   The type of the None singleton.

    `task: _asyncio.Task`
    :   The type of the None singleton.

`MonitorManager(*, db: JobDB, queue: Any)`
:   Manage periodic monitor tasks.
    
    Monitors are persisted in sqlite (monitors table) for auditability.
    Active monitor loops are kept in-memory; on restart, monitors are not
    automatically resumed (restart-safe by default).

    ### Methods

    `get_monitor(self, monitor_id: str) ‑> Dict[str, Any] | None`
    :

    `is_active(self, monitor_id: str) ‑> bool`
    :

    `list_monitors(self, limit: int = 50) ‑> List[Dict[str, Any]]`
    :

    `start_monitor(self, *, interval_s: int, filters: Dict[str, Any], options: Dict[str, Any]) ‑> Dict[str, Any]`
    :   Create and start a monitor.

    `stop_monitor(self, monitor_id: str) ‑> Dict[str, Any]`
    :   Stop a running monitor.