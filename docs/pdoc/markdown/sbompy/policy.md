Module sbompy.policy
====================
Policy validation for SBOMPY deploy-mode.

This is intentionally minimal: it blocks obviously dangerous compose options.
You can extend it with allowlists (registries/namespaces) later.

Classes
-------

`ComposePolicy(allow_privileged: bool = False, allow_host_network: bool = False, allow_host_mounts: bool = False)`
:   Validates docker-compose YAML for safe-ish local testing.
    
    This does NOT make running untrusted containers safe. It merely blocks common
    foot-guns (host networking, privileged, host mounts).

    ### Methods

    `validate_yaml(self, compose_yaml: str) ‑> List[sbompy.policy.PolicyViolation]`
    :

`PolicyViolation(path: str, message: str)`
:   Represents a policy violation found in a compose file.

    ### Instance variables

    `message: str`
    :   The type of the None singleton.

    `path: str`
    :   The type of the None singleton.