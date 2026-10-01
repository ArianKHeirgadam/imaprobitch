"""Validation contract for WGR-CDP dataset manifests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REQUIRED_DATASET_FIELDS = frozenset(
    {
        "dataset_id",
        "source",
        "assay",
        "genome_build",
        "n_tumor",
        "n_normal",
        "stage_available",
        "normal_type",
        "access",
        "license",
        "notes",
        "status",
    }
)

VALID_DATASET_STATUSES = frozenset({"usable", "partial", "unavailable"})


def validate_dataset_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the required dataset-manifest contract.

    Validation is structural only; it does not claim that a dataset is
    biologically suitable or locally available.
    """
    missing = REQUIRED_DATASET_FIELDS - set(manifest)
    if missing:
        raise ValueError(f"missing required dataset fields: {sorted(missing)}")

    result = dict(manifest)

    for field_name in ("dataset_id", "source", "assay", "genome_build", "access", "license", "status"):
        if not str(result[field_name]).strip():
            raise ValueError(f"{field_name} is required")

    if result["status"] not in VALID_DATASET_STATUSES:
        raise ValueError(
            f"invalid dataset status: {result['status']!r}; "
            f"expected one of {sorted(VALID_DATASET_STATUSES)}"
        )

    for field_name in ("n_tumor", "n_normal"):
        value = result[field_name]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{field_name} must be a non-negative integer")

    if not isinstance(result["stage_available"], bool):
        raise ValueError("stage_available must be boolean")

    if not isinstance(result["notes"], str):
        raise ValueError("notes must be a string")

    return result
