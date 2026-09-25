from wgr_cdp.tracking.run import create_run_record
from wgr_cdp.tracking.config_snapshot import snapshot_config
from wgr_cdp.tracking.history import append_history


def test_run_record_creation():
    record = create_run_record({"mode": "test"})

    assert "run_id" in record
    assert record["config"]["mode"] == "test"


def test_config_snapshot_and_history():
    config = snapshot_config({"stage": "evaluation"})
    history = append_history([], {"config": config})

    assert history[0]["config"]["stage"] == "evaluation"
