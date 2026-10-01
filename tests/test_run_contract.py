import pytest

from wgr_cdp.run_contract import (
    RunRecord,
    create_run_record,
    mark_run_complete,
    validate_run_record,
)
from wgr_cdp.status import CONDITIONAL, DATA_UNAVAILABLE, PASS


def test_create_run_record_generates_utc_timestamp():
    run = create_run_record("run-001", {"project": "TCGA-STAD"})
    assert run.run_id == "run-001"
    assert run.workflow_status == CONDITIONAL
    assert run.config["project"] == "TCGA-STAD"
    assert run.created_at.endswith("+00:00")


def test_run_record_round_trip():
    run = RunRecord("run-001", "2026-10-01T00:00:00+00:00", {}, CONDITIONAL)
    assert run.to_dict()["run_id"] == "run-001"


def test_missing_run_field_rejected():
    with pytest.raises(ValueError):
        validate_run_record(
            {
                "run_id": "run-001",
                "created_at": "now",
                "config": {},
            }
        )


def test_config_must_be_mapping():
    with pytest.raises(ValueError):
        RunRecord("run-001", "now", [], CONDITIONAL)


def test_invalid_workflow_status_rejected():
    with pytest.raises(ValueError):
        RunRecord("run-001", "now", {}, DATA_UNAVAILABLE)


def test_validate_run_record_preserves_config():
    result = validate_run_record(
        {
            "run_id": "run-001",
            "created_at": "2026-10-01T00:00:00+00:00",
            "config": {"seed": 42},
            "workflow_status": CONDITIONAL,
        }
    )
    assert result["config"]["seed"] == 42


def test_mark_run_complete_only_changes_workflow_status():
    original = {
        "run_id": "run-001",
        "created_at": "2026-10-01T00:00:00+00:00",
        "config": {"seed": 42},
        "workflow_status": CONDITIONAL,
    }
    result = mark_run_complete(original)
    assert result["workflow_status"] == PASS
    assert result["config"] == {"seed": 42}
