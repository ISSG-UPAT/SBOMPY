"""
SQLite persistence for job state.

Production hardening goals:
- Survive container restarts (jobs list should not disappear).
- Persist minimal job metadata and pointers to artifact run directories.

Design:
- Store job status transitions and summary in sqlite.
- Store SBOM contents on disk (/data/sboms/<run_id>/...), not in sqlite.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  state TEXT NOT NULL,
  created_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  output_dir TEXT NOT NULL,
  run_id TEXT,
  error TEXT,
  summary_json TEXT,
  results_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(state);

CREATE TABLE IF NOT EXISTS monitors (
  monitor_id TEXT PRIMARY KEY,
  state TEXT NOT NULL,
  created_at TEXT NOT NULL,
  started_at TEXT,
  stopped_at TEXT,
  interval_s INTEGER NOT NULL,
  last_scan_at TEXT,
  error TEXT,
  filters_json TEXT,
  options_json TEXT,
  seen_json TEXT,
  triggered_jobs INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_monitors_state ON monitors(state);

"""


class JobDB:
    """A small sqlite wrapper for job state persistence."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        with self._conn:
            self._conn.executescript(SCHEMA)

    def upsert_job(self, job: Dict[str, Any]) -> None:
        """Insert or update a job record."""
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO jobs (job_id,state,created_at,started_at,finished_at,output_dir,run_id,error,summary_json,results_json)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(job_id) DO UPDATE SET
                  state=excluded.state,
                  started_at=excluded.started_at,
                  finished_at=excluded.finished_at,
                  output_dir=excluded.output_dir,
                  run_id=excluded.run_id,
                  error=excluded.error,
                  summary_json=excluded.summary_json,
                  results_json=excluded.results_json
                """,
                (
                    job["job_id"],
                    job["state"],
                    job["created_at"],
                    job.get("started_at"),
                    job.get("finished_at"),
                    job.get("output_dir", ""),
                    job.get("run_id"),
                    job.get("error"),
                    json.dumps(job.get("summary", {})),
                    (
                        json.dumps(job.get("results"))
                        if job.get("results") is not None
                        else None
                    ),
                ),
            )

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a job by id."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT job_id,state,created_at,started_at,finished_at,output_dir,run_id,error,summary_json,results_json FROM jobs WHERE job_id=?",
                (job_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {
            "job_id": row[0],
            "state": row[1],
            "created_at": row[2],
            "started_at": row[3],
            "finished_at": row[4],
            "output_dir": row[5],
            "run_id": row[6],
            "error": row[7],
            "summary": json.loads(row[8]) if row[8] else {},
            "results": json.loads(row[9]) if row[9] else None,
        }

    def list_recent(self, limit: int = 50) -> list[Dict[str, Any]]:
        """List recent jobs."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT job_id,state,created_at,started_at,finished_at,output_dir,run_id,error,summary_json FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        out = []
        for r in rows:
            out.append(
                {
                    "job_id": r[0],
                    "state": r[1],
                    "created_at": r[2],
                    "started_at": r[3],
                    "finished_at": r[4],
                    "output_dir": r[5],
                    "run_id": r[6],
                    "error": r[7],
                    "summary": json.loads(r[8]) if r[8] else {},
                }
            )
        return out

    def mark_incomplete_as_failed(self, reason: str) -> int:
        """
        Mark queued/running jobs as failed (e.g., after restart).

        Returns:
            number of jobs updated
        """
        with self._lock, self._conn:
            cur = self._conn.execute(
                "UPDATE jobs SET state='failed', error=? WHERE state IN ('queued','running')",
                (reason,),
            )
            return cur.rowcount

    # ---- monitors (periodic scanning) ----

    def upsert_monitor(self, monitor: Dict[str, Any]) -> None:
        """Insert or update a monitor record."""
        filters_json = json.dumps(monitor.get("filters_json") or {})
        options_json = json.dumps(monitor.get("options_json") or {})
        seen_json = json.dumps(monitor.get("seen_json") or {"digests": []})
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO monitors(
                monitor_id, state, created_at, started_at, stopped_at,
                interval_s, last_scan_at, error,
                filters_json, options_json, seen_json, triggered_jobs
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(monitor_id) DO UPDATE SET
                state=excluded.state,
                started_at=excluded.started_at,
                stopped_at=excluded.stopped_at,
                interval_s=excluded.interval_s,
                last_scan_at=excluded.last_scan_at,
                error=excluded.error,
                filters_json=excluded.filters_json,
                options_json=excluded.options_json,
                seen_json=excluded.seen_json,
                triggered_jobs=excluded.triggered_jobs
                """,
                (
                    monitor["monitor_id"],
                    monitor["state"],
                    monitor["created_at"],
                    monitor.get("started_at"),
                    monitor.get("stopped_at"),
                    int(monitor.get("interval_s") or 60),
                    monitor.get("last_scan_at"),
                    monitor.get("error"),
                    filters_json,
                    options_json,
                    seen_json,
                    int(monitor.get("triggered_jobs") or 0),
                ),
            )

    def get_monitor(self, monitor_id: str) -> Optional[Dict[str, Any]]:
        """Get a monitor record by id."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT monitor_id, state, created_at, started_at, stopped_at, interval_s, last_scan_at, error, filters_json, options_json, seen_json, triggered_jobs FROM monitors WHERE monitor_id=?",
                (monitor_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {
            "monitor_id": row[0],
            "state": row[1],
            "created_at": row[2],
            "started_at": row[3],
            "stopped_at": row[4],
            "interval_s": int(row[5]),
            "last_scan_at": row[6],
            "error": row[7],
            "filters_json": json.loads(row[8] or "{}"),
            "options_json": json.loads(row[9] or "{}"),
            "seen_json": json.loads(row[10] or "{}"),
            "triggered_jobs": int(row[11] or 0),
        }

    def list_monitors(self, limit: int = 50) -> list[Dict[str, Any]]:
        """List recent monitors."""
        limit = max(1, min(int(limit), 200))
        with self._lock:
            cur = self._conn.execute(
                "SELECT monitor_id, state, created_at, started_at, stopped_at, interval_s, last_scan_at, error, filters_json, options_json, seen_json, triggered_jobs FROM monitors ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        out: list[Dict[str, Any]] = []
        for row in rows:
            out.append(
                {
                    "monitor_id": row[0],
                    "state": row[1],
                    "created_at": row[2],
                    "started_at": row[3],
                    "stopped_at": row[4],
                    "interval_s": int(row[5]),
                    "last_scan_at": row[6],
                    "error": row[7],
                    "filters_json": json.loads(row[8] or "{}"),
                    "options_json": json.loads(row[9] or "{}"),
                    "seen_json": json.loads(row[10] or "{}"),
                    "triggered_jobs": int(row[11] or 0),
                }
            )
        return out
