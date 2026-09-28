"""Hardened pipeline orchestration runner."""

from .config import DEFAULT_STAGES, validate_stages
from .errors import PipelineExecutionError
from .stages import run_stage


def _validate_stage_result(stage, result):
    if not isinstance(result, dict):
        raise PipelineExecutionError(
            stage,
            TypeError("stage must return a dictionary"),
        )

    if result.get("stage") != stage:
        raise PipelineExecutionError(
            stage,
            ValueError("stage result contains an unexpected stage name"),
        )

    if result.get("status") != "completed":
        raise PipelineExecutionError(
            stage,
            ValueError("stage did not complete successfully"),
        )


def execute_pipeline(payload, stages=None, fail_fast=True):
    """Execute stages sequentially with validation and controlled failures.

    The default call remains backward compatible with the original runner.
    When ``fail_fast`` is False, a failed stage is represented in the result
    list and execution stops because downstream stages cannot safely consume
    the failed payload.
    """
    if payload is None:
        raise ValueError("payload is required")

    stage_sequence = validate_stages(
        DEFAULT_STAGES if stages is None else stages
    )

    results = []
    current = payload

    for stage in stage_sequence:
        try:
            result = run_stage(stage, current)
            _validate_stage_result(stage, result)
        except Exception as exc:
            if fail_fast:
                if isinstance(exc, PipelineExecutionError):
                    raise
                raise PipelineExecutionError(stage, exc) from exc

            results.append({
                "stage": stage,
                "status": "failed",
                "error": str(exc),
            })
            break

        results.append(result)
        current = result

    return results
