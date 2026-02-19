# Production hardening checklist

## 1) Network exposure

- Bind on internal interface only, or restrict via firewall / reverse proxy.
- Prefer deploying behind an authenticated gateway (Keycloak/nginx/Caddy).

## 2) Authentication

- Set `SBOMPY_API_KEY` and require `X-API-Key` on clients.
- Rotate the key and store it as a secret.

## 3) Docker socket risk

Mounting `/var/run/docker.sock` effectively grants control over the host Docker daemon.

Mitigations:

- Run SBOMPY only on dedicated internal hosts.
- Use label allow-list (`sand5g.managed=true`) so untrusted containers are ignored.
- Consider a _proxy_ daemon that exposes only read-only endpoints if you need stronger isolation.

## 4) Container hardening

The provided `docker-compose.yml` enables:

- `read_only: true` + `tmpfs: /tmp`
- `cap_drop: [ALL]`
- `no-new-privileges:true`
- run as non-root user (uid 10001)

## 5) Resource controls

- Set CPU/memory limits in compose/kubernetes.
- Keep `SBOMPY_WORKERS` low if SBOM tools are heavy.

## 6) Data retention

- SBOM runs are stored under `/data/sboms/<run_id>/`.
- Add a cron/retention job to delete older run directories if needed.
