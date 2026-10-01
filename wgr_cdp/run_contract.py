"""Canonical execution-run contract for WGR-CDP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .status import CONDITIONAL, PASS, validate_workflow_status


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    created_at: str
    config: Mapping[str, Any]
    workflow_status: str = CONDITIONAL

    def __post_init__(self) -> None:
        if not str(self.run_id).strip():
            raise ValueError("run_id is required")
        if not str(self.created_at).strip():
            raise ValueError("created_at is required")
        if not isinstance(self.config, Mapping):
            raise ValueError("config must be a mapping")
        validate_workflow_status(self.workflow_status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "config": dict(self.config),
            "workflow_status": self.workflow_status,
        }


def create_run_record(
    run_id: str,
    config: Mapping[str, Any] | None = None,
    *,
    workflow_status: str = CONDITIONAL,
    created_at: str | None = None,
) -> RunRecord:
    """Create a validated run record with an explicit UTC creation time."""
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    return RunRecord(
        run_id=run_id,
        created_at=timestamp,
        config=dict(config or {}),
        workflow_status=workflow_status,
    )


def validate_run_record(record: Mapping[str, Any]) -> dict[str, Any]:
    required = {"run_id", "created_at", "config", "workflow_status"}
    missing = required - set(record)
    if missing:
        raise ValueError(f"missing run fields: {sorted(missing)}")

    result = dict(record)
    if not str(result["run_id"]).strip():
        raise ValueError("run_id is required")
    if not str(result["created_at"]).strip():
        raise ValueError("created_at is required")
    if not isinstance(result["config"], Mapping):
        raise ValueError("config must be a mapping")
    validate_workflow_status(result["workflow_status"])
    return result


def mark_run_complete(record: Mapping[str, Any]) -> dict[str, Any]:
    """Mark a validated run as PASS without altering its configuration."""
    result = validate_run_record(record)
    result["workflow_status"] = PASS
    return result
