"""
Docker integration for SBOMPY.

SBOMPY expects access to the Docker daemon via:
  - /var/run/docker.sock mounted into the container

This module:
- lists running containers
- applies label/namespace/compose filtering
- resolves image references and stable identifiers (repo digest / image id)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import docker


def _client() -> docker.DockerClient:
    """Create a Docker client from the environment (uses DOCKER_HOST if set)."""
    return docker.from_env()


def docker_info_safe() -> Dict[str, Any]:
    """
    Return a small, non-sensitive subset of docker daemon info.

    This is useful for audit trails in index.json, without dumping everything.
    """
    c = _client()
    try:
        info = c.info()
        return {
            "ID": info.get("ID"),
            "Name": info.get("Name"),
            "ServerVersion": info.get("ServerVersion"),
            "OperatingSystem": info.get("OperatingSystem"),
            "KernelVersion": info.get("KernelVersion"),
        }
    except Exception:
        return {}


def list_running_containers() -> List[Any]:
    """Return currently running containers."""
    c = _client()
    return c.containers.list()  # running by default


def _match_labels(container_labels: Dict[str, str], required: Dict[str, str]) -> bool:
    """Exact-match label subset check."""
    for k, v in required.items():
        if container_labels.get(k) != v:
            return False
    return True


def filter_containers(
    containers: List[Any],
    *,
    labels: Dict[str, str],
    compose_project: Optional[str],
    namespace: Optional[str],
    namespace_label_key: str,
    require_label_key: Optional[str],
    require_label_value: Optional[str],
) -> List[Any]:
    """
    Filter containers by allow-list and selection criteria.

    Production hardening:
      - require_label_key/value acts as an allow-list gate (e.g., sand5g.managed=true)
    """
    out: List[Any] = []

    for ct in containers:
        lbs = ct.labels or {}

        # allow-list gate
        if require_label_key:
            if require_label_key not in lbs:
                continue
            if (
                require_label_value is not None
                and lbs.get(require_label_key) != require_label_value
            ):
                continue

        if labels and not _match_labels(lbs, labels):
            continue

        if compose_project:
            if lbs.get("com.docker.compose.project") != compose_project:
                continue

        if namespace:
            if lbs.get(namespace_label_key) != namespace:
                continue

        out.append(ct)

    return out


def image_digest_from_image(image: Any) -> Optional[str]:
    """
    Prefer a repo digest (sha256:...) when available.

    Repo digests are stable identifiers for caching SBOMs.
    Fallbacks:
      - image.id (often sha256:...)
    """
    try:
        attrs = image.attrs or {}
        repo_digests = attrs.get("RepoDigests") or []
        if repo_digests:
            # "repo@sha256:..." -> "sha256:..."
            if "@sha256:" in repo_digests[0]:
                return repo_digests[0].split("@", 1)[1]
        return getattr(image, "id", None)
    except Exception:
        return getattr(image, "id", None)


def resolve_images(
    containers: List[Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Build:
      - container_map: name -> {id, image_ref, image_id, digest, labels}
      - images: unique by digest (or image_id), each with list of container names

    Returns:
        (container_map, images)
    """
    container_map: Dict[str, Any] = {}
    by_key: Dict[str, Dict[str, Any]] = {}

    for ct in containers:
        tags = getattr(ct.image, "tags", []) or []
        image_id = getattr(ct.image, "id", None)
        digest = image_digest_from_image(ct.image)

        image_ref = tags[0] if tags else (digest or image_id or "unknown")

        container_map[ct.name] = {
            "id": ct.id,
            "image_ref": image_ref,
            "image_tags": tags,
            "image_id": image_id,
            "digest": digest,
            "labels": ct.labels or {},
        }

        key = digest or image_id or image_ref
        if key not in by_key:
            by_key[key] = {
                "image_ref": image_ref,
                "image_id": image_id,
                "digest": digest,
                "containers": [ct.name],
            }
        else:
            by_key[key]["containers"].append(ct.name)

    images = list(by_key.values())
    images.sort(key=lambda x: (x.get("digest") or "", x.get("image_ref") or ""))
    return container_map, images
