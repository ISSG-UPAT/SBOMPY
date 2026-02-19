# Operations

## Docker

Mount:

- `/var/run/docker.sock:/var/run/docker.sock` (required for discovery)
- `/data` as a persistent volume (required for persistence)

## Concurrency

Set `SBOMPY_WORKERS` to limit concurrent SBOM runs.
Default: 2

## Auth

If `SBOMPY_API_KEY` is set:

- include header `X-API-Key: <key>` on all endpoints except `/health`

## Label allow-list

By default, SBOMPY only scans containers that have:

- `sand5g.managed=true`

You can adjust the allow-list in requests by changing:

- `filters.require_label_key`
- `filters.require_label_value`
