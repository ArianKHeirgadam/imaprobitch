"""Canonical multimodal feature record schema for WGR-CDP."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from .status import DATA_UNAVAILABLE
from .status_validation import validate_feature_status


@dataclass(frozen=True)
class FeatureRecord:
    """Common representation shared by all biological feature modalities."""

    patient: str
    region: str
    feature_type: str
    value: Any
    status: str = DATA_UNAVAILABLE
    gene: str | None = None
    sample: str | None = None
    stage: str | None = None
    tumor_fraction: float | None = None
    depth: float | None = None
    error_rate: float | None = None
    assay: str | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.patient).strip():
            raise ValueError("patient is required")
        if not str(self.region).strip():
            raise ValueError("region is required")
        if not str(self.feature_type).strip():
            raise ValueError("feature_type is required")
        validate_feature_status(self.status)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["provenance"] = dict(self.provenance)
        return result


REQUIRED_FEATURE_FIELDS = frozenset(
    {"patient", "region", "feature_type", "value", "status"}
)


def validate_feature_schema(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize a common feature record."""
    missing = REQUIRED_FEATURE_FIELDS - set(record)
    if missing:
        raise ValueError(f"missing required feature fields: {sorted(missing)}")

    normalized = dict(record)
    normalized["status"] = validate_feature_status(normalized["status"])
    for field_name in ("patient", "region", "feature_type"):
        if not str(normalized[field_name]).strip():
            raise ValueError(f"{field_name} is required")
    if "provenance" in normalized and normalized["provenance"] is None:
        normalized["provenance"] = {}
    return normalized


def feature_record_from_mapping(record: Mapping[str, Any]) -> FeatureRecord:
    """Build a typed feature record after schema validation."""
    normalized = validate_feature_schema(record)
    return FeatureRecord(**normalized)
