Module sbompy.inputs
====================
Input normalization for SBOMPY v1 jobs.

This module turns user-provided image refs or compose YAML into a normalized
plan:
- a list of image refs to scan
- an optional compose file on disk (for deploy-mode)

Classes
-------

`InputNormalizer(workspace: Path)`
:   Normalizes v1 JobCreateRequest inputs.

    ### Methods

    `from_compose_yaml(self, compose_yaml: str, env: Dict[str, str] | None = None) ‑> sbompy.inputs.NormalizedInput`
    :

    `from_image_refs(self, image_refs: List[str]) ‑> sbompy.inputs.NormalizedInput`
    :

`NormalizedInput(kind: str, image_refs: List[str], compose_file: Optional[Path] = None, input_hash: str = '')`
:   Normalized representation of a job input.

    ### Instance variables

    `compose_file: pathlib._local.Path | None`
    :   The type of the None singleton.

    `image_refs: List[str]`
    :   The type of the None singleton.

    `input_hash: str`
    :   The type of the None singleton.

    `kind: str`
    :   The type of the None singleton.