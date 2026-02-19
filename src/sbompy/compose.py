"""
Compose orchestration helpers for SBOMPY (sbompy).

This module provides a small wrapper around `docker compose` (v2) for
ephemeral deployments used in "deploy" mode jobs.

Security note:
Deploying untrusted compose/images can be dangerous. The caller should enforce
policy checks before running `up`.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ComposeUpResult:
    """Result metadata from a compose up/down lifecycle."""
    project: str
    services: List[str]
    ps_json: Optional[str] = None


class ComposeOrchestrator:
    """
    Orchestrates docker compose operations via the CLI.

    This intentionally uses the CLI to avoid tight coupling to compose internals.
    """

    def __init__(self, compose_file: Path, project: str, workdir: Optional[Path] = None):
        self.compose_file = compose_file
        self.project = project
        self.workdir = workdir or compose_file.parent

    def _run(self, args: List[str], timeout_s: int = 600) -> subprocess.CompletedProcess:
        cmd = ["docker", "compose", "-f", str(self.compose_file), "-p", self.project, *args]
        return subprocess.run(
            cmd,
            cwd=str(self.workdir),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )

    def up(self, build: bool = False, pull_policy: str = "if-not-present", timeout_s: int = 600) -> ComposeUpResult:
        """
        Bring up the compose project in detached mode.
        """
        args = ["up", "-d"]
        if build:
            args.append("--build")
        # pull policy supported by compose v2: --pull <policy>
        if pull_policy in ("always", "missing", "if-not-present", "never"):
            # compose uses "missing" and "always"; accept if-not-present as alias
            pol = "missing" if pull_policy == "if-not-present" else pull_policy
            args.extend(["--pull", pol])
        cp = self._run(args, timeout_s=timeout_s)
        if cp.returncode != 0:
            raise RuntimeError(f"docker compose up failed: {cp.stderr.strip() or cp.stdout.strip()}")
        services = self.services(timeout_s=timeout_s)
        return ComposeUpResult(project=self.project, services=services)

    def down(self, remove_volumes: bool = True, timeout_s: int = 600) -> None:
        """
        Stop and remove the compose project.
        """
        args = ["down", "--remove-orphans"]
        if remove_volumes:
            args.append("-v")
        cp = self._run(args, timeout_s=timeout_s)
        if cp.returncode != 0:
            raise RuntimeError(f"docker compose down failed: {cp.stderr.strip() or cp.stdout.strip()}")

    def services(self, timeout_s: int = 60) -> List[str]:
        cp = self._run(["config", "--services"], timeout_s=timeout_s)
        if cp.returncode != 0:
            return []
        return [l.strip() for l in cp.stdout.splitlines() if l.strip()]

    def ps_json(self, timeout_s: int = 60) -> str:
        cp = self._run(["ps", "--format", "json"], timeout_s=timeout_s)
        if cp.returncode != 0:
            return "[]"
        return cp.stdout.strip() or "[]"
