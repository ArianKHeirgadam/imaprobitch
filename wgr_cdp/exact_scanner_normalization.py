"""Canonical normalization helpers for exact scanner inputs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

REQUIRED_INPUT_FIELDS = frozenset({"patient", "region", "value"})


def normalize_feature_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one scanner input without changing its biological meaning."""
    missing = REQUIRED_INPUT_FIELDS - set(record)
    if missing:
        raise ValueError(f"missing scanner input fields: {sorted(missing)}")

    result = dict(record)

    for field in ("patient", "region"):
        value = result[field]
        if value is None or not str(value).strip():
            raise ValueError(f"{field} is required")
        result[field] = str(value).strip()

    if result.get("feature_type") is not None:
        result["feature_type"] = str(result["feature_type"]).strip()

    return result


def normalize_scanner_inputs(
    records: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize scanner records while preserving input order."""
    return [normalize_feature_record(record) for record in records]


def deduplicate_scanner_inputs(
    records: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Remove exact duplicate patient/region/value records deterministically."""
    normalized = normalize_scanner_inputs(records)
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, Any]] = []

    for record in normalized:
        key = (
            record["patient"],
            record["region"],
            repr(record["value"]),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(record)

    return result
