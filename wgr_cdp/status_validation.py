"""Validation helpers for the canonical WGR-CDP status contract.

This module provides the integration boundary used by feature-producing
pipelines. Biological feature statuses and workflow statuses are validated
separately so a workflow outcome cannot be mistaken for biological evidence.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping

from .status import (
    DATA_UNAVAILABLE,
    validate_feature_status,
    validate_workflow_status,
)


def validate_feature_record(record: Mapping[str, object]) -> dict[str, object]:
    """Return a validated copy of a feature record."""
    result = dict(record)
    result["status"] = validate_feature_status(result.get("status", DATA_UNAVAILABLE))
    return result


def validate_feature_records(
    records: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Validate a collection of feature records."""
    return [validate_feature_record(record) for record in records]


def set_feature_status(
    record: MutableMapping[str, object],
    status: object,
) -> MutableMapping[str, object]:
    """Set only a canonical biological feature status."""
    record["status"] = validate_feature_status(status)
    return record


def set_workflow_status(
    record: MutableMapping[str, object],
    status: object,
) -> MutableMapping[str, object]:
    """Set only a canonical workflow status."""
    record["status"] = validate_workflow_status(status)
    return record
