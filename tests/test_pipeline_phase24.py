import pytest

from wgr_cdp.pipeline.config import validate_stages
from wgr_cdp.pipeline.errors import PipelineExecutionError
from wgr_cdp.pipeline.runner import execute_pipeline
import wgr_cdp.pipeline.runner as runner


def test_pipeline_accepts_custom_stage_sequence():
    results = execute_pipeline(
        {"sample": "sample_001"},
        stages=["manifest", "qc"],
    )

    assert [result["stage"] for result in results] == ["manifest", "qc"]


def test_pipeline_rejects_invalid_stage_configuration():
    with pytest.raises(ValueError):
        validate_stages([])

    with pytest.raises(ValueError):
        validate_stages(["manifest", "manifest"])

    with pytest.raises(TypeError):
        validate_stages("manifest")


def test_pipeline_rejects_missing_payload():
    with pytest.raises(ValueError):
        execute_pipeline(None)


def test_pipeline_wraps_stage_failure(monkeypatch):
    def failing_stage(name, payload):
        raise RuntimeError("network unavailable")

    monkeypatch.setattr(runner, "run_stage", failing_stage)

    with pytest.raises(PipelineExecutionError) as exc_info:
        execute_pipeline({"sample": "sample_001"}, stages=["manifest"])

    assert exc_info.value.stage == "manifest"
    assert "network unavailable" in str(exc_info.value)


def test_pipeline_non_fail_fast_records_failure(monkeypatch):
    def failing_stage(name, payload):
        raise RuntimeError("temporary failure")

    monkeypatch.setattr(runner, "run_stage", failing_stage)

    results = execute_pipeline(
        {"sample": "sample_001"},
        stages=["manifest", "qc"],
        fail_fast=False,
    )

    assert results == [{
        "stage": "manifest",
        "status": "failed",
        "error": "temporary failure",
    }]
