"""
Digest-based SBOM cache.

Production hardening:
- Cache key includes digest + tool + format.
- Cache stored under /data/cache/ (mounted volume recommended)

This avoids recomputing SBOMs for the same image digest.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


def cache_key(digest: str, tool: str, fmt: str) -> str:
    safe_digest = digest.replace(":", "_")
    return f"{safe_digest}/{tool}/{fmt}.json"


def cache_path(base: Path, digest: str, tool: str, fmt: str) -> Path:
    return base / "cache" / cache_key(digest, tool, fmt)


def read_cache(base: Path, digest: Optional[str], tool: str, fmt: str) -> Optional[Dict[str, Any]]:
    if not digest:
        return None
    p = cache_path(base, digest, tool, fmt)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_cache(base: Path, digest: Optional[str], tool: str, fmt: str, data: Dict[str, Any]) -> Optional[Path]:
    if not digest:
        return None
    p = cache_path(base, digest, tool, fmt)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p
