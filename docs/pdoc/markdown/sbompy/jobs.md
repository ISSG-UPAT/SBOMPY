Module sbompy.jobs
==================
Job orchestration and background workers.

Production hardening features:
- Persistent job state via sqlite (/data/sbompy.sqlite)
- Worker queue with bounded concurrency (SBOMPY_WORKERS, default 2)
- Job recovery: on startup, queued/running jobs are marked failed (restart-safe)
- Output artifacts always written to /data/sboms/<run_id>/...

Note:
SBOMPY intentionally keeps the worker model simple and self-contained
(no external Redis/Celery dependency) for easy deployment inside SAND5G VMs.

Functions
---------

`make_run_id(job_id: str) ‑> str`
:   

`utcnow_iso() ‑> str`
:   

Classes
-------

`JobQueue(base_dir: Path)`
:   In-process job queue with background workers.
    
    Jobs are persisted in sqlite; the queue holds only job_ids and parameters.

    ### Methods

    `create_job(self) ‑> Dict[str, Any]`
    :

    `enqueue(self, job_id: str, payload: Dict[str, Any]) ‑> None`
    :

    `get_job(self, job_id: str) ‑> Dict[str, Any] | None`
    :

    `list_recent(self, limit: int = 50) ‑> list[typing.Dict[str, typing.Any]]`
    :

    `start(self) ‑> None`
    :

    `stop(self) ‑> None`
    :

    `utcnow_iso(self) ‑> str`
    :   Return current UTC time in ISO 8601 format.