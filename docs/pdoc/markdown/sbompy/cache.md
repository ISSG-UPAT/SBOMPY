Module sbompy.cache
===================
Digest-based SBOM cache.

Production hardening:
- Cache key includes digest + tool + format.
- Cache stored under /data/cache/ (mounted volume recommended)

This avoids recomputing SBOMs for the same image digest.

Functions
---------

`cache_key(digest: str, tool: str, fmt: str) ‑> str`
:   

`cache_path(base: Path, digest: str, tool: str, fmt: str) ‑> pathlib._local.Path`
:   

`read_cache(base: Path, digest: Optional[str], tool: str, fmt: str) ‑> Dict[str, Any] | None`
:   

`write_cache(base: Path, digest: Optional[str], tool: str, fmt: str, data: Dict[str, Any]) ‑> pathlib._local.Path | None`
: