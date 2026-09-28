"""Pipeline configuration and validation."""

DEFAULT_STAGES = [
    "manifest",
    "qc",
    "variant",
    "features",
    "annotation",
    "fusion",
    "discovery",
    "evaluation",
]


def validate_stages(stages):
    """Validate an execution stage sequence."""
    if not isinstance(stages, (list, tuple)):
        raise TypeError("stages must be a list or tuple")

    normalized = [str(stage) for stage in stages]

    if not normalized:
        raise ValueError("stages must not be empty")

    if any(not stage for stage in normalized):
        raise ValueError("stage names must not be empty")

    if len(set(normalized)) != len(normalized):
        raise ValueError("stage names must be unique")

    return normalized
