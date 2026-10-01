"""Canonical input/output artifact contracts for WGR-CDP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .status import DATA_UNAVAILABLE, validate_workflow_status


@dataclass(frozen=True)
class InputArtifact:
    artifact_id: str
    path: str
    artifact_type: str
    status: str = DATA_UNAVAILABLE
    checksum: str | None = None

    def __post_init__(self) -> None:
        for name in ("artifact_id", "path", "artifact_type"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "path": self.path,
            "artifact_type": self.artifact_type,
            "status": self.status,
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class OutputArtifact:
    artifact_id: str
    path: str
    artifact_type: str
    workflow_status: str
    schema_version: str

    def __post_init__(self) -> None:
        for name in ("artifact_id", "path", "artifact_type", "schema_version"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        validate_workflow_status(self.workflow_status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "path": self.path,
            "artifact_type": self.artifact_type,
            "workflow_status": self.workflow_status,
            "schema_version": self.schema_version,
        }


def validate_input_artifact(record: Mapping[str, Any]) -> dict[str, Any]:
    required = {"artifact_id", "path", "artifact_type"}
    missing = required - set(record)
    if missing:
        raise ValueError(f"missing input artifact fields: {sorted(missing)}")
    result = dict(record)
    for field in required:
        if not str(result[field]).strip():
            raise ValueError(f"{field} is required")
    if "status" not in result:
        result["status"] = DATA_UNAVAILABLE
    return result


def validate_output_artifact(record: Mapping[str, Any]) -> dict[str, Any]:
    required = {"artifact_id", "path", "artifact_type", "workflow_status", "schema_version"}
    missing = required - set(record)
    if missing:
        raise ValueError(f"missing output artifact fields: {sorted(missing)}")
    result = dict(record)
    validate_workflow_status(result["workflow_status"])
    for field in required - {"workflow_status"}:
        if not str(result[field]).strip():
            raise ValueError(f"{field} is required")
    return result
