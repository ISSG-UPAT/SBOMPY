Module sbompy.db
================
SQLite persistence for job state.

Production hardening goals:
- Survive container restarts (jobs list should not disappear).
- Persist minimal job metadata and pointers to artifact run directories.

Design:
- Store job status transitions and summary in sqlite.
- Store SBOM contents on disk (/data/sboms/<run_id>/...), not in sqlite.

Classes
-------

`JobDB(db_path: Path)`
:   A small sqlite wrapper for job state persistence.

    ### Methods

    `get_job(self, job_id: str) ‑> Dict[str, Any] | None`
    :   Fetch a job by id.

    `get_monitor(self, monitor_id: str) ‑> Dict[str, Any] | None`
    :   Get a monitor record by id.

    `list_monitors(self, limit: int = 50) ‑> list[typing.Dict[str, typing.Any]]`
    :   List recent monitors.

    `list_recent(self, limit: int = 50) ‑> list[typing.Dict[str, typing.Any]]`
    :   List recent jobs.

    `mark_incomplete_as_failed(self, reason: str) ‑> int`
    :   Mark queued/running jobs as failed (e.g., after restart).
        
        Returns:
            number of jobs updated

    `upsert_job(self, job: Dict[str, Any]) ‑> None`
    :   Insert or update a job record.

    `upsert_monitor(self, monitor: Dict[str, Any]) ‑> None`
    :   Insert or update a monitor record.