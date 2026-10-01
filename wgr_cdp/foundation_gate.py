"""Foundation integration gate for WGR-CDP contracts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .artifact_contract import validate_input_artifact, validate_output_artifact
from .dataset_manifest import validate_dataset_manifest
from .dataset_status import DATASET_STATUSES
from .feature_schema import validate_feature_schema
from .provenance import validate_provenance
from .run_contract import validate_run_record
from .status import FEATURE_STATUSES, WORKFLOW_STATUSES
from .traceability import validate_trace_record


def validate_foundation_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the cross-contract foundation bundle.

    This is a structural integration gate only. It does not validate
    biological correctness or empirical scientific results.
    """
    required = {
        "dataset",
        "feature",
        "provenance",
        "run",
        "trace",
        "input_artifact",
        "output_artifact",
    }
    missing = required - set(bundle)
    if missing:
        raise ValueError(f"missing foundation sections: {sorted(missing)}")

    result = dict(bundle)
    result["dataset"] = validate_dataset_manifest(result["dataset"])
    result["feature"] = validate_feature_schema(result["feature"])
    result["provenance"] = validate_provenance(result["provenance"])
    result["run"] = validate_run_record(result["run"])
    result["trace"] = validate_trace_record(result["trace"])
    result["input_artifact"] = validate_input_artifact(result["input_artifact"])
    result["output_artifact"] = validate_output_artifact(result["output_artifact"])

    if result["run"]["run_id"] != result["trace"]["run_id"]:
        raise ValueError("run_id mismatch between run and trace")

    if result["input_artifact"]["artifact_id"] not in result["trace"]["input_artifact_ids"]:
        raise ValueError("input artifact is not linked to trace")

    if result["output_artifact"]["artifact_id"] not in result["trace"]["output_artifact_ids"]:
        raise ValueError("output artifact is not linked to trace")

    if result["feature"]["status"] not in FEATURE_STATUSES:
        raise ValueError("invalid feature status")

    if result["run"]["workflow_status"] not in WORKFLOW_STATUSES:
        raise ValueError("invalid workflow status")

    if result["dataset"]["status"] not in DATASET_STATUSES:
        raise ValueError("invalid dataset status")

    return result
