Module sbompy.auth
==================
Authentication helpers.

Production hardening:
- If SBOMPY_API_KEY is set, all non-health endpoints require header: X-API-Key: <key>
- If not set, endpoints are unauthenticated (intended for internal-only deployments)

This is intentionally simple; in SAND5G you may place SBOMPY behind a reverse proxy (nginx/Caddy/Keycloak).

Functions
---------

`require_api_key(x_api_key: str | None = Header(None)) ‑> None`
:   FastAPI dependency that enforces an API key if configured.
    
    Args:
        x_api_key: Value of the 'X-API-Key' header.
    
    Raises:
        HTTPException: 401 if API key is configured and missing/wrong.