from wgr_cdp.release import RELEASE_METADATA, run_health_check
from wgr_cdp.release.report import build_release_report


def test_release_metadata_is_research_scoped():
    assert RELEASE_METADATA["release"] == "1.0.0"
    assert RELEASE_METADATA["status"] == "research"
    assert RELEASE_METADATA["clinical_diagnostic"] is False


def test_release_health_check_passes():
    result = run_health_check()

    assert result["passed"] is True
    assert all(result["checks"].values())


def test_release_report_contains_health_state():
    health = run_health_check()
    report = build_release_report(health, test_count=62)

    assert report["release"] == "1.0.0"
    assert report["passed"] is True
    assert report["test_count"] == 62
