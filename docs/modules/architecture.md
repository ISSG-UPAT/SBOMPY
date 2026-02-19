# Architecture

SBOMPY is a small, self-contained SBOM trigger service intended to run inside a container.

## Components

- **FastAPI server**: receives triggers and provides status endpoints.
- **Docker discovery**: reads running containers and image identifiers via the Docker socket.
- **Worker queue**: processes SBOM runs asynchronously with bounded concurrency.
- **Tool backend**: executes `syft` or `trivy` as subprocesses.
- **Persistence**
  - Job state: sqlite at `/data/sbompy.sqlite`
  - Artifacts: `/data/sboms/<run_id>/...`
  - Cache: `/data/cache/<digest>/<tool>/<format>.json`

## Data flow

1. Client calls `/sbom/run`
2. SBOMPY creates a job record (sqlite), enqueues it, returns `job_id`
3. Worker discovers eligible containers (unless explicit images are provided)
4. Worker resolves image digest/id and checks cache
5. Worker runs SBOM tool when cache miss
6. Worker writes artifacts + index.json
7. Worker updates job state to `done` or `failed`

## Security considerations

Mounting `/var/run/docker.sock` grants significant host control to the SBOMPY container.
Deploy SBOMPY on internal networks and protect it with:

- `SBOMPY_API_KEY` or a reverse proxy with SSO
- label allow-list (default: `sand5g.managed=true`)
- network policies / firewall rules
