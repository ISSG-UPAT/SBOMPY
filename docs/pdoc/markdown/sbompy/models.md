Module sbompy.models
====================
Pydantic models for SBOMPY's API surface.

SBOMPY focuses on:
- Discovering Docker containers/images on the host (via the Docker socket)
- Generating SBOMs via an external tool (syft or trivy)
- Persisting artifacts and job state for operational robustness

Classes
-------

`ComposeJobInput(**data: Any)`
:   Compose input for v1 jobs.
    
    Provide compose YAML content directly (best for API usage).
    File upload endpoints may store the compose file and pass a path instead.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `compose_yaml: str`
    :   The type of the None singleton.

    `env: Dict[str, str]`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `type: Literal['compose']`
    :   The type of the None singleton.

`DeployOptions(**data: Any)`
:   Options controlling ephemeral docker compose deployment.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `build: bool`
    :   The type of the None singleton.

    `enabled: bool`
    :   The type of the None singleton.

    `health_wait_seconds: int`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `pull_policy: Literal['always', 'if-not-present', 'never']`
    :   The type of the None singleton.

    `remove_volumes: bool`
    :   The type of the None singleton.

`DiscoverImage(**data: Any)`
:   !!! abstract "Usage Documentation"
        [Models](../concepts/models.md)
    
    A base class for creating Pydantic models.
    
    Attributes:
        __class_vars__: The names of the class variables defined on the model.
        __private_attributes__: Metadata about the private attributes of the model.
        __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.
    
        __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
        __pydantic_core_schema__: The core schema of the model.
        __pydantic_custom_init__: Whether the model has a custom `__init__` function.
        __pydantic_decorators__: Metadata containing the decorators defined on the model.
            This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
        __pydantic_generic_metadata__: Metadata for generic models; contains data used for a similar purpose to
            __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.
        __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
        __pydantic_post_init__: The name of the post-init method for the model, if defined.
        __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
        __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
        __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.
    
        __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
        __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.
    
        __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
            is set to `'allow'`.
        __pydantic_fields_set__: The names of fields explicitly set during instantiation.
        __pydantic_private__: Values of private attributes set on the model instance.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `containers: List[str]`
    :   The type of the None singleton.

    `digest: str | None`
    :   The type of the None singleton.

    `image_id: str | None`
    :   The type of the None singleton.

    `image_ref: str`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

`DiscoverRequest(**data: Any)`
:   Request payload for /sbom/discover.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `filters: sbompy.models.FilterSpec`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

`DiscoverResponse(**data: Any)`
:   !!! abstract "Usage Documentation"
        [Models](../concepts/models.md)
    
    A base class for creating Pydantic models.
    
    Attributes:
        __class_vars__: The names of the class variables defined on the model.
        __private_attributes__: Metadata about the private attributes of the model.
        __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.
    
        __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
        __pydantic_core_schema__: The core schema of the model.
        __pydantic_custom_init__: Whether the model has a custom `__init__` function.
        __pydantic_decorators__: Metadata containing the decorators defined on the model.
            This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
        __pydantic_generic_metadata__: Metadata for generic models; contains data used for a similar purpose to
            __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.
        __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
        __pydantic_post_init__: The name of the post-init method for the model, if defined.
        __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
        __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
        __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.
    
        __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
        __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.
    
        __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
            is set to `'allow'`.
        __pydantic_fields_set__: The names of fields explicitly set during instantiation.
        __pydantic_private__: Values of private attributes set on the model instance.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `containers: Dict[str, Any]`
    :   The type of the None singleton.

    `images: List[sbompy.models.DiscoverImage]`
    :   The type of the None singleton.

    `matched_container_count: int`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

`FilterSpec(**data: Any)`
:   Container selection filters.
    
    SBOMPY intentionally filters at the container layer (labels),
    because this is the most reliable way to target only "vertical" workloads.
    
    Typical usage in SAND5G:
      - sand5g.namespace=<vertical>
      - sand5g.managed=false
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `compose_project: str | None`
    :   The type of the None singleton.

    `labels: Dict[str, str]`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `namespace: str | None`
    :   The type of the None singleton.

    `namespace_label_key: str`
    :   The type of the None singleton.

    `require_label_key: str | None`
    :   The type of the None singleton.

    `require_label_value: str | None`
    :   The type of the None singleton.

`ImageJobInput(**data: Any)`
:   Image input for v1 jobs.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `image_refs: List[str]`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `type: Literal['image']`
    :   The type of the None singleton.

`JobCreateRequest(**data: Any)`
:   Create a v1 job.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `input: sbompy.models.ImageJobInput | sbompy.models.ComposeJobInput`
    :   The type of the None singleton.

    `mode: Literal['static', 'deploy']`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `options: sbompy.models.JobOptions`
    :   The type of the None singleton.

`JobOptions(**data: Any)`
:   Options shared by static and deploy modes.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `deploy: sbompy.models.DeployOptions`
    :   The type of the None singleton.

    `format: Literal['cyclonedx-json', 'spdx-json', 'syft-json', 'trivy-cyclonedx-json', 'trivy-spdx-json']`
    :   The type of the None singleton.

    `include_docker_info: bool`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `timeout_s: int`
    :   The type of the None singleton.

    `tool: Literal['syft', 'trivy']`
    :   The type of the None singleton.

`JobResponse(**data: Any)`
:   !!! abstract "Usage Documentation"
        [Models](../concepts/models.md)
    
    A base class for creating Pydantic models.
    
    Attributes:
        __class_vars__: The names of the class variables defined on the model.
        __private_attributes__: Metadata about the private attributes of the model.
        __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.
    
        __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
        __pydantic_core_schema__: The core schema of the model.
        __pydantic_custom_init__: Whether the model has a custom `__init__` function.
        __pydantic_decorators__: Metadata containing the decorators defined on the model.
            This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
        __pydantic_generic_metadata__: Metadata for generic models; contains data used for a similar purpose to
            __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.
        __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
        __pydantic_post_init__: The name of the post-init method for the model, if defined.
        __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
        __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
        __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.
    
        __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
        __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.
    
        __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
            is set to `'allow'`.
        __pydantic_fields_set__: The names of fields explicitly set during instantiation.
        __pydantic_private__: Values of private attributes set on the model instance.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `job: sbompy.models.JobStatus`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `results: Dict[str, Any] | None`
    :   The type of the None singleton.

`JobStatus(**data: Any)`
:   !!! abstract "Usage Documentation"
        [Models](../concepts/models.md)
    
    A base class for creating Pydantic models.
    
    Attributes:
        __class_vars__: The names of the class variables defined on the model.
        __private_attributes__: Metadata about the private attributes of the model.
        __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.
    
        __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
        __pydantic_core_schema__: The core schema of the model.
        __pydantic_custom_init__: Whether the model has a custom `__init__` function.
        __pydantic_decorators__: Metadata containing the decorators defined on the model.
            This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
        __pydantic_generic_metadata__: Metadata for generic models; contains data used for a similar purpose to
            __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.
        __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
        __pydantic_post_init__: The name of the post-init method for the model, if defined.
        __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
        __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
        __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.
    
        __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
        __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.
    
        __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
            is set to `'allow'`.
        __pydantic_fields_set__: The names of fields explicitly set during instantiation.
        __pydantic_private__: Values of private attributes set on the model instance.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `created_at: str`
    :   The type of the None singleton.

    `error: str | None`
    :   The type of the None singleton.

    `finished_at: str | None`
    :   The type of the None singleton.

    `job_id: str`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `output_dir: str`
    :   The type of the None singleton.

    `run_id: str | None`
    :   The type of the None singleton.

    `started_at: str | None`
    :   The type of the None singleton.

    `state: Literal['queued', 'running', 'done', 'failed']`
    :   The type of the None singleton.

    `summary: Dict[str, Any]`
    :   The type of the None singleton.

`MonitorCreateRequest(**data: Any)`
:   Create a periodic monitor that scans for new running images.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `filters: sbompy.models.MonitorFilters`
    :   The type of the None singleton.

    `interval_s: int`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `options: sbompy.models.MonitorOptions`
    :   The type of the None singleton.

`MonitorFilters(**data: Any)`
:   Filters applied when scanning running containers.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `compose_project: str | None`
    :   The type of the None singleton.

    `labels: Dict[str, str]`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `namespace: str | None`
    :   The type of the None singleton.

    `namespace_label_key: str`
    :   The type of the None singleton.

    `require_label_key: str | None`
    :   The type of the None singleton.

    `require_label_value: str | None`
    :   The type of the None singleton.

`MonitorOptions(**data: Any)`
:   SBOM generation options for new images detected by the monitor.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `format: str`
    :   The type of the None singleton.

    `include_docker_info: bool`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `timeout_s: int`
    :   The type of the None singleton.

    `tool: str`
    :   The type of the None singleton.

`MonitorResponse(**data: Any)`
:   Monitor state and metadata.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `created_at: str`
    :   The type of the None singleton.

    `error: str | None`
    :   The type of the None singleton.

    `interval_s: int`
    :   The type of the None singleton.

    `last_scan_at: str | None`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `monitor_id: str`
    :   The type of the None singleton.

    `seen_count: int`
    :   The type of the None singleton.

    `started_at: str | None`
    :   The type of the None singleton.

    `state: str`
    :   The type of the None singleton.

    `stopped_at: str | None`
    :   The type of the None singleton.

    `triggered_jobs: int`
    :   The type of the None singleton.

    ### Static methods

    `from_row(m: Dict[str, Any]) ‑> sbompy.models.MonitorResponse`
    :

`RunRequest(**data: Any)`
:   Request payload for /sbom/run.
    
    If 'images' is provided, SBOMPY runs SBOM generation for those image references
    without container discovery (useful for testing or one-off scans).
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
    validated to form a valid model.
    
    `self` is explicitly positional-only to allow `self` as a field name.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel

    ### Class variables

    `filters: sbompy.models.FilterSpec`
    :   The type of the None singleton.

    `format: Literal['cyclonedx-json', 'spdx-json', 'syft-json', 'trivy-cyclonedx-json', 'trivy-spdx-json']`
    :   The type of the None singleton.

    `images: List[str] | None`
    :   The type of the None singleton.

    `include_docker_info: bool`
    :   The type of the None singleton.

    `model_config`
    :   The type of the None singleton.

    `timeout_s: int`
    :   The type of the None singleton.

    `tool: Literal['syft', 'trivy']`
    :   The type of the None singleton.