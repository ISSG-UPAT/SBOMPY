"""
Policy validation for SBOMPY deploy-mode.

This is intentionally minimal: it blocks obviously dangerous compose options.
You can extend it with allowlists (registries/namespaces) later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import yaml


@dataclass
class PolicyViolation:
    """Represents a policy violation found in a compose file."""

    path: str
    message: str


class ComposePolicy:
    """
    Validates docker-compose YAML for safe-ish local testing.

    This does NOT make running untrusted containers safe. It merely blocks common
    foot-guns (host networking, privileged, host mounts).
    """

    def __init__(
        self,
        allow_privileged: bool = False,
        allow_host_network: bool = False,
        allow_host_mounts: bool = False,
    ):
        self.allow_privileged = allow_privileged
        self.allow_host_network = allow_host_network
        self.allow_host_mounts = allow_host_mounts

    def validate_yaml(self, compose_yaml: str) -> List[PolicyViolation]:
        obj = yaml.safe_load(compose_yaml) or {}
        if not isinstance(obj, dict):
            return [PolicyViolation(path="$", message="compose YAML must be a mapping")]

        violations: List[PolicyViolation] = []
        services = obj.get("services") or {}
        if not isinstance(services, dict):
            return [
                PolicyViolation(path="services", message="services must be a mapping")
            ]

        for svc_name, svc in services.items():
            if not isinstance(svc, dict):
                continue
            pfx = f"services.{svc_name}"

            if svc.get("privileged") and not self.allow_privileged:
                violations.append(
                    PolicyViolation(
                        path=f"{pfx}.privileged",
                        message="privileged containers are not allowed",
                    )
                )

            net_mode = svc.get("network_mode")
            if (
                isinstance(net_mode, str)
                and net_mode.strip().lower() == "host"
                and not self.allow_host_network
            ):
                violations.append(
                    PolicyViolation(
                        path=f"{pfx}.network_mode",
                        message="host networking is not allowed",
                    )
                )

            vols = svc.get("volumes") or []
            if vols and not self.allow_host_mounts:
                # block anything that looks like a host bind mount "<host>:<container>"
                for i, v in enumerate(vols):
                    if isinstance(v, str) and ":" in v:
                        host = v.split(":", 1)[0].strip()
                        if (
                            host.startswith("/")
                            or host.startswith(".")
                            or host.startswith("~")
                        ):
                            violations.append(
                                PolicyViolation(
                                    path=f"{pfx}.volumes[{i}]",
                                    message="host bind mounts are not allowed",
                                )
                            )
        return violations
