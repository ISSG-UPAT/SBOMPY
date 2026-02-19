"""
SBOM tool backends.

SBOMPY delegates SBOM generation to external tools executed as subprocesses.

Supported:
- syft
- trivy (SBOM mode for images)

Return format:
- Always JSON-decoded objects on success.
- Structured error dictionaries on failure.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, Literal

SbomTool = Literal["syft", "trivy"]


def _run(cmd: list[str], timeout_s: int) -> Dict[str, Any]:
    """Run a command and attempt to parse stdout as JSON."""
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "cmd": cmd}
    except FileNotFoundError:
        raise

    if p.returncode != 0:
        return {
            "ok": False,
            "error": "tool_failed",
            "exit_code": p.returncode,
            "cmd": cmd,
            "stderr": (p.stderr or "")[-4000:],
        }

    try:
        return {"ok": True, "json": json.loads(p.stdout)}
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": "invalid_json_output",
            "cmd": cmd,
            "stdout_tail": (p.stdout or "")[-2000:],
            "stderr_tail": (p.stderr or "")[-2000:],
        }


def generate_sbom(
    tool: SbomTool, image_ref: str, fmt: str, timeout_s: int
) -> Dict[str, Any]:
    """
    Generate an SBOM for a docker image reference.

    Args:
        tool: "syft" or "trivy"
        image_ref: e.g., "nginx:latest" or a digest/image id
        fmt:
            - syft: cyclonedx-json | spdx-json | syft-json
            - trivy: trivy-cyclonedx-json | trivy-spdx-json
        timeout_s: Subprocess timeout

    Returns:
        A dict:
          - {"ok": True, "json": <sbom>}
          - {"ok": False, ...}
    """
    if tool == "syft":
        # ensure no "trivy-" prefix leaks in
        fmt2 = fmt.replace("trivy-", "")
        cmd = ["syft", image_ref, "-o", fmt2]
        return _run(cmd, timeout_s)

    if tool == "trivy":
        if fmt == "trivy-cyclonedx-json":
            cmd = [
                "trivy",
                "image",
                "--format",
                "cyclonedx",
                "--output",
                "-",
                image_ref,
            ]
        elif fmt == "trivy-spdx-json":
            cmd = [
                "trivy",
                "image",
                "--format",
                "spdx-json",
                "--output",
                "-",
                image_ref,
            ]
        else:
            return {"ok": False, "error": "unsupported_format_for_trivy", "format": fmt}
        return _run(cmd, timeout_s)

    return {"ok": False, "error": "unsupported_tool", "tool": tool}
