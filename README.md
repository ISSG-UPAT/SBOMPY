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

### Development Setup

```bash
git clone https://github.com/ISSG-UPAT/SBOMPY.git
cd SBOMPY
make setup-all-dev
make test
sbompy
```

This creates a virtual environment, installs all dependencies, runs tests, and starts the server.

## Installation

### From Source

```bash
git clone https://github.com/ISSG-UPAT/SBOMPY.git
cd SBOMPY
pip install .
```

### Development Installation

```bash
pip install -e .[dev,docs]
```

### Using Makefile

The project includes a comprehensive Makefile for development:

```bash
make help                    # Show all available targets
make setup-all-dev          # Create venv + install all dependencies
make test                   # Run tests
make doc-pdoc               # Generate documentation
make docker-build           # Build Docker image
```

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

### Discover Containers

```bash
curl -X POST http://localhost:8080/sbom/discover \
  -H 'Content-Type: application/json' \
  -d '{"filters":{"compose_project":"open5gs","require_label_key":"sand5g.managed","require_label_value":"true"}}'
```

### Generate SBOMs

```bash
curl -X POST http://localhost:8080/sbom/run \
  -H 'Content-Type: application/json' \
  -d '{"tool":"syft","format":"cyclonedx-json","filters":{"namespace":"vertical-a"}}'
```

### Check Job Status

```bash
curl http://localhost:8080/jobs/{job_id}
```

## Development

### Running Tests

```bash
make test
# or
pytest
```

### Code Quality

```bash
# Lint with ruff
ruff check .

# Format code
ruff format .
```

### Documentation

```bash
# Generate API docs with pdoc
make doc-pdoc

# Host docs locally
make doc-pdoc-host
```

FastAPI automatic docs are available at `http://localhost:8080/docs`.

## Docker Deployment

### Build Images

```bash
make docker-build          # Standard image
make docker-build-alpine   # Alpine-based image
make docker-build-modified # Modified image (used in compose)
```

### Docker Compose

The included `docker-compose.yml` provides a production-ready setup with:

- Persistent data volume
- Security hardening (read-only, dropped capabilities)
- Docker socket access for container scanning

```bash
make compose-up    # Start services
make compose-down  # Stop services
```

## Project Structure

```
├── src/sbompy/              # Main package
│   ├── api.py             # FastAPI application
│   ├── auth.py            # Authentication middleware
│   ├── cache.py           # Digest-based caching
│   ├── db.py              # SQLite database operations
│   ├── docker_client.py   # Docker API client
│   ├── jobs.py            # Background job processing
│   ├── main.py            # Application entry point
│   ├── models.py          # Pydantic models
│   ├── storage.py         # File storage operations
│   └── tools.py           # SBOM tool integrations
├── docker/                # Docker configurations
├── docs/                  # Documentation
├── tests/                 # Test suite
└── pyproject.toml         # Project configuration
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

Copyright (c) 2026 ISSG University of Patras

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run `make test` to ensure everything works
6. Submit a pull request

Issues and pull requests are welcome!
