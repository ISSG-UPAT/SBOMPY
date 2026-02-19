Module sbompy.compose
=====================
Compose orchestration helpers for SBOMPY (sbompy).

This module provides a small wrapper around `docker compose` (v2) for
ephemeral deployments used in "deploy" mode jobs.

Security note:
Deploying untrusted compose/images can be dangerous. The caller should enforce
policy checks before running `up`.

Classes
-------

`ComposeOrchestrator(compose_file: Path, project: str, workdir: Optional[Path] = None)`
:   Orchestrates docker compose operations via the CLI.
    
    This intentionally uses the CLI to avoid tight coupling to compose internals.

    ### Methods

    `down(self, remove_volumes: bool = True, timeout_s: int = 600) ‑> None`
    :   Stop and remove the compose project.

    `ps_json(self, timeout_s: int = 60) ‑> str`
    :

    `services(self, timeout_s: int = 60) ‑> List[str]`
    :

    `up(self, build: bool = False, pull_policy: str = 'if-not-present', timeout_s: int = 600) ‑> sbompy.compose.ComposeUpResult`
    :   Bring up the compose project in detached mode.

`ComposeUpResult(project: str, services: List[str], ps_json: Optional[str] = None)`
:   Result metadata from a compose up/down lifecycle.

    ### Instance variables

    `project: str`
    :   The type of the None singleton.

    `ps_json: str | None`
    :   The type of the None singleton.

    `services: List[str]`
    :   The type of the None singleton.