from wgr_cdp.validation.gate import run_quality_gate


def test_quality_gate_pass():
    result = run_quality_gate({
        "run_id": "run_001",
        "summary": {},
        "metrics": {},
        "artifacts": [],
    })

    assert result["passed"] is True
    assert result["checks"]["schema"] is True


def test_quality_gate_fail():
    result = run_quality_gate({
        "summary": {},
        "metrics": None,
    })

    assert result["passed"] is False
