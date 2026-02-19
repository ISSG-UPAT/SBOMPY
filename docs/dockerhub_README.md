# SBOMPY

## About

This Python package was developed in the **SAND5G** project, which aims to enhance security in 5G networks.

SBOMPY is a Python-based, FastAPI service that can be **triggered via HTTP** to generate **SBOMs** for the
Docker workloads currently running on a host. It is designed for platform-style deployments where
verticals are deployed as containers and must be scanned and recorded as part of the operational flow.

**Repository**: https://github.com/ISSG-UPAT/SBOMPY  
**Project Website**: https://sand5g-project.eu  
![SAND5G](https://sand5g-project.eu/wp-content/uploads/2024/06/SAND5G-logo-600x137.png)

## Overview

SBOMPY runs as a container and connects to the host Docker daemon via the Docker socket. When triggered,
it discovers eligible containers, resolves their image identifiers (preferably digests), and generates
SBOMs using an external tool backend (**syft** or **trivy**). Outputs are persisted under `/data`
for later ingestion by the platform.

## Features

- **RESTful API** with FastAPI for SBOM generation
- **Asynchronous job processing** with background workers
- **Container discovery** with filtering capabilities
- **SBOM generation** using Syft or Trivy backends
- **Deduplication** via digest-based caching
- **Persistent storage** with SQLite database
- **Production hardening** features
- **API key authentication** (optional)

### API Endpoints

- `GET /health` - Health check
- `POST /sbom/discover` - Preview containers to be scanned
- `POST /sbom/run` - Start async SBOM generation job
- `GET /jobs/{job_id}` - Poll job status and results
- `GET /jobs` - List recent jobs
- `GET /sbom/artifacts` - List all SBOM artifacts
- `GET /sbom/artifacts/{run_id}` - Get specific run artifacts

## Requirements

- Python 3.11+
- Docker access via socket mount: `/var/run/docker.sock:/var/run/docker.sock`
- For Docker deployment: persistent volume mount for `/data`

## Quick Start

### Using Docker Compose (Recommended)

```bash
git clone https://github.com/ISSG-UPAT/SBOMPY.git
cd SBOMPY
make compose-up
```

The service will be available at `http://localhost:8080`.

## Configuration

SBOMPY is configured via environment variables:

| Variable                | Default     | Description                         |
| ----------------------- | ----------- | ----------------------------------- |
| `SBOMPY_HOST`           | `0.0.0.0`   | Server host                         |
| `SBOMPY_PORT`           | `8080`      | Server port                         |
| `SBOMPY_API_KEY`        | -           | Optional API key for authentication |
| `SBOMPY_WORKERS`        | `2`         | Number of background workers        |
| `SBOMPY_TOOL_DEFAULT`   | `syft`      | Default SBOM tool                   |
| `SBOMPY_FORMAT_DEFAULT` | `syft-json` | Default output format               |

### Filtering and Allow-lists

Container discovery uses Docker labels for filtering:

- **Allow-list label**: `sand5g.managed=true` (default)
- **Namespace label**: `sand5g.namespace=<vertical>`

## Usage Examples

### Health Check

```bash
curl http://localhost:8080/health
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

Copyright (c) 2026 ISSG University of Patras
