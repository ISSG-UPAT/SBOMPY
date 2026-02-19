Module sbompy.tools
===================
SBOM tool backends.

SBOMPY delegates SBOM generation to external tools executed as subprocesses.

Supported:
- syft
- trivy (SBOM mode for images)

Return format:
- Always JSON-decoded objects on success.
- Structured error dictionaries on failure.

Functions
---------

`generate_sbom(tool: SbomTool, image_ref: str, fmt: str, timeout_s: int) ‑> Dict[str, Any]`
:   Generate an SBOM for a docker image reference.
    
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