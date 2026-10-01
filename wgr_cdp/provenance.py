"""Canonical provenance contract for WGR-CDP feature records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Provenance:
    """Minimum audit trail required for a feature-producing operation."""

    source: str
    source_file: str
    source_record: str
    genome_build: str
    created_at: str
    run_id: str

    def __post_init__(self) -> None:
        for field_name, value in asdict(self).items():
            if not str(value).strip():
                raise ValueError(f"{field_name} is required")

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


REQUIRED_PROVENANCE_FIELDS = frozenset(
    {"source", "source_file", "source_record", "genome_build", "created_at", "run_id"}
)


def validate_provenance(provenance: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a provenance mapping and return a copy."""
    missing = REQUIRED_PROVENANCE_FIELDS - set(provenance)
    if missing:
        raise ValueError(f"missing provenance fields: {sorted(missing)}")

    normalized = dict(provenance)
    for field_name in REQUIRED_PROVENANCE_FIELDS:
        if not str(normalized[field_name]).strip():
            raise ValueError(f"{field_name} is required")
    return normalized


def provenance_from_mapping(provenance: Mapping[str, Any]) -> Provenance:
    """Build a typed provenance record after validation."""
    normalized = validate_provenance(provenance)
    return Provenance(**normalized)
