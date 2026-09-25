from wgr_cdp.reporting.generator import generate_report


def test_report_generation():
    report = generate_report(
        "run_001",
        {"status": "completed"},
        {"score": 0.9},
        ["artifact.json"],
    )

    assert report["status"] == "generated"
    assert report["report"]["run_id"] == "run_001"
    assert report["report"]["metrics"]["score"] == 0.9
