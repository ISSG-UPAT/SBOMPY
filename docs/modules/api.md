# API

## POST /sbom/discover

Preview scan plan for eligible running containers.

Request body:
- `filters.labels`: exact label match
- `filters.compose_project`: match `com.docker.compose.project`
- `filters.namespace`: match namespace label value (default label key: `sand5g.namespace`)
- allow-list gate: `filters.require_label_key/value`

## POST /sbom/run

Start an asynchronous SBOM run.

Request body:
- `tool`: `syft` | `trivy`
- `format`: syft formats or `trivy-*` formats
- `timeout_s`
- `filters` as above
- `images`: optional explicit image refs to scan (bypasses discovery)

Returns:
- `job_id` and initial state.

## GET /jobs/{job_id}

Poll job state.

- `queued` → `running` → (`done` | `failed`)
- When finished, `results.index_path` points to the stored `index.json`.

## GET /sbom/artifacts

List persisted run directories.

## GET /sbom/artifacts/{run_id}

Return the stored `index.json` for that run.
