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


def test_benchmark_and_sweep():
    from wgr_cdp.research.benchmark import benchmark, benchmark_by_feature, parameter_sweep, recall_vs_cost

    def exact(data):
        return exact_scan(data)

    def fast(data):
        return coarse_to_fine_scan(data)

    result = benchmark(exact, fast, rows())
    assert {"recall", "precision", "exact_runtime_s", "fast_runtime_s",
            "exact_peak_bytes", "fast_peak_bytes", "tp", "fp", "fn"} <= result.keys()
    assert 0 <= result["recall"] <= 1
    assert 0 <= result["precision"] <= 1

    by_feature = benchmark_by_feature(exact, fast, rows())
    assert "SNV" in by_feature

    sweep = parameter_sweep(
        exact,
        lambda threshold: lambda data: coarse_to_fine_scan(data, effect_threshold=threshold),
        rows(),
        [0.0, 0.1, 0.2],
    )
    assert len(sweep) == 3
    assert all("fast_runtime_s" in item and "recall" in item for item in sweep)
    assert recall_vs_cost(sweep)


def test_blood_background_source_separation():
    from wgr_cdp.research.blood_background import estimate_background, filter_candidates, annotate_background_sources
    data = [
        {"region": "1:100-100", "healthy_plasma": 0.02, "wbc": 0.01, "gnomad": 0.005},
        {"region": "1:100-100", "healthy_plasma": 0.03, "chip": 0.20},
        {"region": "1:200-200"},
    ]
    background = estimate_background(data)
    assert background["1:100-100"]["healthy_plasma"]["max"] == 0.03
    assert background["1:100-100"]["wbc"]["status"] == "Available"
    assert background["1:100-100"]["pon"]["status"] == "Data unavailable"
    assert background["1:200-200"]["wbc"]["status"] == "Data unavailable"
    kept, rejected = filter_candidates([{"region": "1:100-100"}, {"region": "1:200-200"}], background, max_background=0.10)
    assert len(kept) == 1
    assert len(rejected) == 1
    assert kept[0]["blood_background_status"] == "Data unavailable"
    annotated = annotate_background_sources([{"region": "1:100-100"}], background)
    assert annotated[0]["blood_background_sources"]["chip"]["max"] == 0.20

def test_pdf_requirements_a1_a3():
    from wgr_cdp.research.multires_scanner import exact_scan, coarse_to_fine_scan
    from wgr_cdp.research.benchmark import benchmark_summary
    from wgr_cdp.research.blood_background import estimate_background

    exact_a = exact_scan(rows())
    exact_b = exact_scan(rows())
    assert exact_a == exact_b
    result = coarse_to_fine_scan(rows())
    assert all(item["exact_checked"] for item in result["final"])
    assert set(result["resolutions"]) == {"5Mb", "1Mb", "100kb", "10kb", "1kb", "base"}
    assert all("parent_region" in item and "screening_effect" in item for item in result["lineage"])
    summary = benchmark_summary(exact_scan, coarse_to_fine_scan, rows())
    assert "fast_resolution_evaluated" in summary
    assert summary["by_feature_type"]["SNV"]["recall"] >= 0
    bg = estimate_background([{"region":"1:1-10","wbc":0.01,"feature_type":"METHYLATION"},
                              {"region":"1:1-10","chip":0.02,"feature_type":"CNV"}])
    assert bg["1:1-10"]["wbc"]["status"] == "Available"
    assert bg["1:1-10"]["pon"]["status"] == "Data unavailable"


def test_pdf_phase_a4_cfdna_requirements():
    from wgr_cdp.research.cfdna import DEFAULT_TUMOR_FRACTIONS, patient_candidate_matrix
    from wgr_cdp.research.cfdna_score_engine import detectability_score, REQUIRED_TUMOR_FRACTIONS
    from wgr_cdp.research.cfdna_simulator import simulate_detectability, validate_analytical_against_simulation

    assert DEFAULT_TUMOR_FRACTIONS == (0.5,0.2,0.1,0.05,0.02,0.01,0.005)
    assert REQUIRED_TUMOR_FRACTIONS == DEFAULT_TUMOR_FRACTIONS
    score = detectability_score(.01, depth=50, region_size=100, informative_sites=4,
                                 copy_number=2, error_rate=.001, blood_background=.02,
                                 feature_type="SNV")
    assert 0 <= score["detectability_score"] <= 1
    assert score["region_size"] == 100
    assert score["assay_feasibility"] == "limited_low_pass_SNV_INDEL"
    analytical = score["detectability_score"]
    simulated = simulate_detectability(.01, depth=50, informative_sites=4, simulations=2000, seed=7)
    check = validate_analytical_against_simulation(analytical, simulated["power"], tolerance=.10)
    assert check["within_tolerance"]
    matrix = patient_candidate_matrix(
        ["P1","P2"], ["c1"],
        {"P1":{"c1":{"present":False}}, "P2":{"c1":{"tumor_fraction":.05,"depth":300}}},
    )
    assert matrix["P1"]["c1"] == 0.0
    assert matrix["P2"]["c1"] > 0
