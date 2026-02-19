Module sbompy.docker_client
===========================
Docker integration for SBOMPY.

SBOMPY expects access to the Docker daemon via:
  - /var/run/docker.sock mounted into the container

This module:
- lists running containers
- applies label/namespace/compose filtering
- resolves image references and stable identifiers (repo digest / image id)

Functions
---------

`docker_info_safe() ‑> Dict[str, Any]`
:   Return a small, non-sensitive subset of docker daemon info.
    
    This is useful for audit trails in index.json, without dumping everything.

`filter_containers(containers: List[Any], *, labels: Dict[str, str], compose_project: Optional[str], namespace: Optional[str], namespace_label_key: str, require_label_key: Optional[str], require_label_value: Optional[str]) ‑> List[Any]`
:   Filter containers by allow-list and selection criteria.
    
    Production hardening:
      - require_label_key/value acts as an allow-list gate (e.g., sand5g.managed=true)

`image_digest_from_image(image: Any) ‑> str | None`
:   Prefer a repo digest (sha256:...) when available.
    
    Repo digests are stable identifiers for caching SBOMs.
    Fallbacks:
      - image.id (often sha256:...)

`list_running_containers() ‑> List[Any]`
:   Return currently running containers.

`resolve_image_ref(image_ref: str, pull: bool = False) ‑> Dict[str, str | None]`
:   Resolve an image reference to a local image id and (if available) repo digest.
    
    Args:
        image_ref: Image reference/tag/digest.
        pull: If True, attempt to pull the image if not present locally.
    
    Returns:
        dict with keys: image_ref, image_id, digest

`resolve_images(containers: List[Any]) ‑> Tuple[Dict[str, Any], List[Dict[str, Any]]]`
:   Build:
      - container_map: name -> {id, image_ref, image_id, digest, labels}
      - images: unique by digest (or image_id), each with list of container names
    
    Returns:
        (container_map, images)