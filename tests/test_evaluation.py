from wgr_cdp.evaluation.statistics import frequency_analysis
from wgr_cdp.evaluation.metrics import confidence_score
from wgr_cdp.evaluation.report import build_report


def test_frequency_analysis():
    result = frequency_analysis(["A", "A", "B"])

    assert result["A"] == 2 / 3


def test_confidence_and_report():
    assert confidence_score(10, 5) == 0.5

    report = build_report("candidate_001", {"score": 0.8})

    assert report["candidate_id"] == "candidate_001"
