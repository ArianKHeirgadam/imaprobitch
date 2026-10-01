"""Semantic helpers for dataset availability states."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

DATASET_USABLE = "usable"
DATASET_PARTIAL = "partial"
DATASET_UNAVAILABLE = "unavailable"

DATASET_STATUSES = frozenset(
    {DATASET_USABLE, DATASET_PARTIAL, DATASET_UNAVAILABLE}
)


def dataset_status_reason(status: str, *, reason: str | None = None) -> str:
    """Return an explicit non-biological explanation for a dataset state."""
    if status not in DATASET_STATUSES:
        raise ValueError(f"invalid dataset status: {status!r}")

    if reason is not None and not str(reason).strip():
        raise ValueError("reason must be non-empty when provided")

    if reason:
        return str(reason)

    return {
        DATASET_USABLE: "dataset metadata and required inputs are available for the declared scope",
        DATASET_PARTIAL: "only part of the declared dataset scope is available",
        DATASET_UNAVAILABLE: "required dataset inputs are unavailable",
    }[status]


def classify_dataset_status(
    manifest: Mapping[str, Any],
    *,
    required_inputs_available: bool,
    partial_inputs_available: bool = False,
) -> str:
    """Classify workflow availability without making biological claims."""
    declared = manifest.get("status")

    if declared not in DATASET_STATUSES:
        raise ValueError(f"invalid dataset status: {declared!r}")

    if required_inputs_available:
        return DATASET_USABLE

    if partial_inputs_available:
        return DATASET_PARTIAL

    return DATASET_UNAVAILABLE


def assert_not_biological_negative(status: str, biological_result: Any) -> None:
    """Prevent unavailable/partial data from being interpreted as a negative finding."""
    if status not in DATASET_STATUSES:
        raise ValueError(f"invalid dataset status: {status!r}")

    if status in {DATASET_PARTIAL, DATASET_UNAVAILABLE}:
        if biological_result in {"Not detected", "negative", "NEGATIVE", False}:
            raise ValueError(
                "dataset availability cannot be converted into negative biological evidence"
            )
