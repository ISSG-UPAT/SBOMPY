Module sbompy.storage
=====================
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

Functions
---------

`list_runs(base: Path) ‑> list[str]`
:   

`make_run_dir(base: Path, run_id: str) ‑> pathlib._local.Path`
:   

`read_run_index(base: Path, run_id: str) ‑> Dict[str, Any]`
:   

`write_index(run_dir: Path, index: Dict[str, Any]) ‑> pathlib._local.Path`
:   

`write_sbom_file(run_dir: Path, key: str, data: Dict[str, Any]) ‑> pathlib._local.Path`
: