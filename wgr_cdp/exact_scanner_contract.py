"""Canonical contract for exact feature scanning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .status import DATA_UNAVAILABLE, validate_feature_status


@dataclass(frozen=True)
class ExactScanRequest:
    feature_type: str
    resolution: int | str
    records: tuple[Mapping[str, Any], ...]
    alpha: float = 0.05

    def __post_init__(self) -> None:
        if not str(self.feature_type).strip():
            raise ValueError("feature_type is required")
        if not self.records:
            raise ValueError("records cannot be empty")
        if not (0 < self.alpha < 1):
            raise ValueError("alpha must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_type": self.feature_type,
            "resolution": self.resolution,
            "records": [dict(row) for row in self.records],
            "alpha": self.alpha,
        }


@dataclass(frozen=True)
class ExactScanResult:
    feature_type: str
    resolution: int | str
    status: str
    candidates: tuple[Mapping[str, Any], ...]
    records_evaluated: int

    def __post_init__(self) -> None:
        validate_feature_status(self.status)
        if self.records_evaluated < 0:
            raise ValueError("records_evaluated must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_type": self.feature_type,
            "resolution": self.resolution,
            "status": self.status,
            "candidates": [dict(row) for row in self.candidates],
            "records_evaluated": self.records_evaluated,
        }


def validate_exact_scan_result(result: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "feature_type",
        "resolution",
        "status",
        "candidates",
        "records_evaluated",
    }
    missing = required - set(result)
    if missing:
        raise ValueError(f"missing exact scan result fields: {sorted(missing)}")

    normalized = dict(result)
    validate_feature_status(normalized["status"])

    if not isinstance(normalized["candidates"], (list, tuple)):
        raise ValueError("candidates must be a list or tuple")

    if (
        not isinstance(normalized["records_evaluated"], int)
        or isinstance(normalized["records_evaluated"], bool)
        or normalized["records_evaluated"] < 0
    ):
        raise ValueError("records_evaluated must be a non-negative integer")

    return normalized


def unavailable_exact_scan_result(
    feature_type: str,
    resolution: int | str,
    *,
    reason: str | None = None,
) -> ExactScanResult:
    candidates: tuple[Mapping[str, Any], ...] = ()
    if reason:
        candidates = ({"status": DATA_UNAVAILABLE, "reason": reason},)
    return ExactScanResult(
        feature_type=feature_type,
        resolution=resolution,
        status=DATA_UNAVAILABLE,
        candidates=candidates,
        records_evaluated=0,
    )
