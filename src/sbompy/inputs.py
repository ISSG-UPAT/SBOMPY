"""
Input normalization for SBOMPY v1 jobs.

This module turns user-provided image refs or compose YAML into a normalized
plan:
- a list of image refs to scan
- an optional compose file on disk (for deploy-mode)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


@dataclass
class NormalizedInput:
    """Normalized representation of a job input."""
    kind: str  # "image" or "compose"
    image_refs: List[str]
    compose_file: Optional[Path] = None
    input_hash: str = ""


class InputNormalizer:
    """
    Normalizes v1 JobCreateRequest inputs.
    """

    def __init__(self, workspace: Path):
        self.workspace = workspace

    @staticmethod
    def _sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def from_image_refs(self, image_refs: List[str]) -> NormalizedInput:
        payload = ("\n".join(image_refs)).encode("utf-8")
        return NormalizedInput(
            kind="image",
            image_refs=image_refs,
            compose_file=None,
            input_hash=self._sha256(payload),
        )

    def from_compose_yaml(self, compose_yaml: str, env: Dict[str, str] | None = None) -> NormalizedInput:
        env = env or {}
        data = compose_yaml.encode("utf-8")
        compose_path = self.workspace / "docker-compose.yml"
        compose_path.write_text(compose_yaml)

        obj = yaml.safe_load(compose_yaml) or {}
        services = (obj.get("services") or {}) if isinstance(obj, dict) else {}
        image_refs: List[str] = []

        for svc_name, svc in services.items():
            if not isinstance(svc, dict):
                continue
            img = svc.get("image")
            if isinstance(img, str) and img.strip():
                image_refs.append(img.strip())

        # Hash should include compose content and env overrides
        env_blob = "\n".join([f"{k}={v}" for k, v in sorted(env.items())]).encode("utf-8")
        input_hash = self._sha256(data + b"\n" + env_blob)

        return NormalizedInput(
            kind="compose",
            image_refs=image_refs,
            compose_file=compose_path,
            input_hash=input_hash,
        )
