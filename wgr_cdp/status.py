"""Canonical status vocabulary for WGR-CDP feature measurements.

Biological measurement status is intentionally separate from workflow/release
status. Missing data must remain explicit and must never be represented as
negative biological evidence.
"""

from __future__ import annotations

from typing import Final

DETECTED: Final[str] = "Detected"
NOT_DETECTED: Final[str] = "Not detected"
DATA_UNAVAILABLE: Final[str] = "Data unavailable"

FEATURE_STATUSES: Final[frozenset[str]] = frozenset(
    {DETECTED, NOT_DETECTED, DATA_UNAVAILABLE}
)

PASS: Final[str] = "PASS"
FAIL: Final[str] = "FAIL"
WARN: Final[str] = "WARN"
CONDITIONAL: Final[str] = "CONDITIONAL"
QUARANTINED: Final[str] = "QUARANTINED"

WORKFLOW_STATUSES: Final[frozenset[str]] = frozenset(
    {PASS, FAIL, WARN, CONDITIONAL, QUARANTINED}
)


def validate_feature_status(status: object) -> str:
    """Return a canonical feature status or raise ValueError."""
    if status in FEATURE_STATUSES:
        return str(status)
    raise ValueError(
        f"invalid feature status {status!r}; "
        f"expected one of {sorted(FEATURE_STATUSES)!r}"
    )


def validate_workflow_status(status: object) -> str:
    """Return a canonical workflow status or raise ValueError."""
    if status in WORKFLOW_STATUSES:
        return str(status)
    raise ValueError(
        f"invalid workflow status {status!r}; "
        f"expected one of {sorted(WORKFLOW_STATUSES)!r}"
    )


def feature_status_from_value(value: object) -> str:
    """Map an absent measurement to Data unavailable.

    This helper deliberately does not infer Not detected from missing values.
    Not detected requires an actual measurement.
    """
    return DATA_UNAVAILABLE if value is None else DETECTED
