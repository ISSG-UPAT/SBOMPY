"""
Artifact storage utilities.

SBOMPY persists each run to:
  /data/sboms/<run_id>/

Contents:
  - index.json (metadata, container snapshot, list of SBOM files, cache stats)
  - sboms/*.json (per-image SBOM wrapper: ok/cached/sbom or error)

This makes it easy for another platform component to:
- scrape artifacts
- ingest index.json into a DB
- ship artifacts to object storage
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def make_run_dir(base: Path, run_id: str) -> Path:
    d = base / "sboms" / run_id
    (d / "sboms").mkdir(parents=True, exist_ok=True)
    return d


def write_index(run_dir: Path, index: Dict[str, Any]) -> Path:
    p = run_dir / "index.json"
    p.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def write_sbom_file(run_dir: Path, key: str, data: Dict[str, Any]) -> Path:
    p = run_dir / "sboms" / f"{key}.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def list_runs(base: Path) -> list[str]:
    sboms_dir = base / "sboms"
    if not sboms_dir.exists():
        return []
    return sorted([p.name for p in sboms_dir.iterdir() if p.is_dir()], reverse=True)


def read_run_index(base: Path, run_id: str) -> Dict[str, Any]:
    p = base / "sboms" / run_id / "index.json"
    return json.loads(p.read_text(encoding="utf-8"))
