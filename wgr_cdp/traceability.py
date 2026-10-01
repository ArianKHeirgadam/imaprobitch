"""Traceability contract linking runs, inputs, and outputs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REQUIRED_TRACE_FIELDS = frozenset(
    {"run_id", "input_artifact_ids", "output_artifact_ids"}
)


def validate_trace_record(record: Mapping[str, Any]) -> dict[str, Any]:
    missing = REQUIRED_TRACE_FIELDS - set(record)
    if missing:
        raise ValueError(f"missing trace fields: {sorted(missing)}")

    result = dict(record)
    if not str(result["run_id"]).strip():
        raise ValueError("run_id is required")

    for field in ("input_artifact_ids", "output_artifact_ids"):
        value = result[field]
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"{field} must be a list or tuple")
        if any(not str(item).strip() for item in value):
            raise ValueError(f"{field} cannot contain blank artifact ids")
        result[field] = list(value)

    if len(set(result["input_artifact_ids"])) != len(result["input_artifact_ids"]):
        raise ValueError("input_artifact_ids must be unique")
    if len(set(result["output_artifact_ids"])) != len(result["output_artifact_ids"]):
        raise ValueError("output_artifact_ids must be unique")

    return result


def build_trace_record(
    run_id: str,
    input_artifact_ids: list[str] | tuple[str, ...],
    output_artifact_ids: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    return validate_trace_record(
        {
            "run_id": run_id,
            "input_artifact_ids": list(input_artifact_ids),
            "output_artifact_ids": list(output_artifact_ids),
        }
    )


def assert_trace_membership(
    trace: Mapping[str, Any],
    *,
    input_artifact_id: str | None = None,
    output_artifact_id: str | None = None,
) -> bool:
    """Check that an artifact belongs to the declared run trace."""
    validated = validate_trace_record(trace)

    if input_artifact_id is not None and input_artifact_id not in validated["input_artifact_ids"]:
        return False
    if output_artifact_id is not None and output_artifact_id not in validated["output_artifact_ids"]:
        return False
    return True
