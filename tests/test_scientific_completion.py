from wgr_cdp.research.cfdna import detectability_probability, estimate_lod, patient_candidate_matrix
from wgr_cdp.research.multires_scanner import exact_scan, coarse_to_fine_scan
from wgr_cdp.research.panel_optimizer import panel_coverage, greedy_panel, ilp_panel, alpha_budget
from wgr_cdp.research.statistics import benjamini_hochberg, cohen_h


def rows():
    return [
        {"patient": "C1", "group": "case", "region": "1:100-100", "feature_type": "SNV", "status": "Detected", "value": 1},
        {"patient": "C2", "group": "case", "region": "1:100-100", "feature_type": "SNV", "status": "Detected", "value": 1},
        {"patient": "H1", "group": "control", "region": "1:100-100", "feature_type": "SNV", "status": "Not detected", "value": 0},
        {"patient": "H2", "group": "control", "region": "1:100-100", "feature_type": "SNV", "status": "Not detected", "value": 0},
    ]


def test_cfdna_monotonic_and_lod():
    assert detectability_probability(.10, depth=300) > detectability_probability(.01, depth=300)
    assert estimate_lod(depth=300) is not None


def test_patient_matrix():
    matrix = patient_candidate_matrix(
        ["P1"], ["c1"], {"c1": {"tumor_fraction": .05, "depth": 300}}
    )
    assert 0 <= matrix["P1"]["c1"] <= 1


def test_scanner():
    result = coarse_to_fine_scan(rows())
    assert len(exact_scan(rows())) == 1
    assert len(result["final"]) == 1
    assert result["resolutions"] == ["5Mb", "1Mb", "100kb", "10kb", "1kb", "base"]
    assert result["exact_checked"] == 1
    assert result["lineage"]
    assert any(item["retained"] for item in result["lineage"])


def test_feature_specific_scanner():
    data = [
        {"patient": "C1", "group": "case", "region": "8:100-200", "feature_type": "CNV", "status": "Detected", "log2_ratio": 0.8},
        {"patient": "C2", "group": "case", "region": "8:100-200", "feature_type": "CNV", "status": "Detected", "log2_ratio": 0.7},
        {"patient": "H1", "group": "control", "region": "8:100-200", "feature_type": "CNV", "status": "Detected", "log2_ratio": 0.0},
        {"patient": "H2", "group": "control", "region": "8:100-200", "feature_type": "CNV", "status": "Detected", "log2_ratio": 0.1},
        {"patient": "C1", "group": "case", "region": "9:100-200", "feature_type": "METHYLATION", "status": "Detected", "value": 0.8},
        {"patient": "C2", "group": "case", "region": "9:100-200", "feature_type": "METHYLATION", "status": "Detected", "value": 0.7},
        {"patient": "H1", "group": "control", "region": "9:100-200", "feature_type": "METHYLATION", "status": "Detected", "value": 0.2},
        {"patient": "H2", "group": "control", "region": "9:100-200", "feature_type": "METHYLATION", "status": "Detected", "value": 0.1},
        {"patient": "C1", "group": "case", "region": "MT:100-101", "feature_type": "MITOCHONDRIAL", "status": "Detected", "heteroplasmy": 0.8},
        {"patient": "C2", "group": "case", "region": "MT:100-101", "feature_type": "MITOCHONDRIAL", "status": "Detected", "heteroplasmy": 0.7},
        {"patient": "H1", "group": "control", "region": "MT:100-101", "feature_type": "MITOCHONDRIAL", "status": "Detected", "heteroplasmy": 0.1},
        {"patient": "H2", "group": "control", "region": "MT:100-101", "feature_type": "MITOCHONDRIAL", "status": "Detected", "heteroplasmy": 0.2},
    ]
    exact = exact_scan(data)
    by_type = {row["feature_type"]: row for row in exact}
    assert set(by_type) == {"CNV", "METHYLATION", "MITOCHONDRIAL"}
    assert by_type["CNV"]["case_mean"] > by_type["CNV"]["control_mean"]
    assert by_type["METHYLATION"]["case_mean"] > by_type["METHYLATION"]["control_mean"]
    assert by_type["MITOCHONDRIAL"]["case_mean"] > by_type["MITOCHONDRIAL"]["control_mean"]


def test_multires_neighbor_lineage():
    result = coarse_to_fine_scan(rows(), neighbor_k=1)
    lineage = result["lineage"]
    assert all("parent_region" in row for row in lineage) or lineage == []
    assert result["exact_checked"] == 1


def test_panel():
    matrix = {"P1": {"a": .9, "b": .1}, "P2": {"a": .1, "b": .9}}
    assert panel_coverage(matrix, ["a", "b"]) > panel_coverage(matrix, ["a"])
    assert len(greedy_panel(matrix, max_k=2)["selected"]) == 2
    assert ilp_panel(matrix, max_k=2)["status"] == "optimal"


def test_statistics():
    assert benjamini_hochberg([.01, .02]) == [.02, .02]
    assert cohen_h(.9, .1) > 0
    assert 0 < alpha_budget(.05, 5) < .05


def test_leakage():
    from wgr_cdp.research.validation import LeakageGuard, AnalysisState, cohort_holdout_guard
    guard = LeakageGuard()
    guard.freeze()
    guard.enter_validation()
    assert guard.state == AnalysisState.VALIDATION
    try:
        cohort_holdout_guard(["A"], ["A"])
        assert False
    except ValueError:
        pass
