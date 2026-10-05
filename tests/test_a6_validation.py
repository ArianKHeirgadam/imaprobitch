from wgr_cdp.research.a6_validation import (
    conventional_feature_ranking, compare_baseline, run_ablations,
    logistic_baseline, elastic_net_coordinate_descent,
    bootstrap_rank_stability, run_a6, evaluate_selected_candidates
)

def candidates():
    return [
        {"feature":"A","q_value":0.001,"detectability":0.9,"blood_background_safety":0.95,
         "early_stage_score":0.8,"specificity_score":0.9,"statistical_strength":0.99,
         "biological_evidence":0.8},
        {"feature":"B","q_value":0.01,"detectability":0.7,"blood_background_safety":0.8,
         "early_stage_score":0.5,"specificity_score":0.6,"statistical_strength":0.9,
         "biological_evidence":0.7},
        {"feature":"C","q_value":0.2,"detectability":0.95,"blood_background_safety":0.99,
         "early_stage_score":0.9,"specificity_score":0.9,"statistical_strength":0.8,
         "biological_evidence":0.6},
    ]

WEIGHTS={"biological_evidence":1,"statistical_strength":1,"detectability":1,
         "blood_background_safety":1,"early_stage_score":1,"specificity_score":1,
         "literature_novelty":1,"literature_validation_gap":1,"literature_diagnostic_utility":1}

def test_conventional_baseline_is_deterministic():
    a=conventional_feature_ranking(candidates(),2)
    b=conventional_feature_ranking(candidates(),2)
    assert [x["feature"] for x in a]==[x["feature"] for x in b]==["A","B"]

def test_baseline_uses_same_candidate_universe():
    ranked=candidates()
    result=compare_baseline(ranked,ranked,matrix=None,k=2)
    assert result["baseline"]["selected"]==["A","B"]
    assert result["wgr_cdp"]["selected"]==["A","B"]
    assert result["overlap"]["overlap"]==2
    assert result["overlap"]["interpretation"]=="selection_overlap_not_predictive_performance"
    assert result["baseline"]["coverage"]=="Data unavailable"

def test_full_ablation_uses_panel_optimization_when_matrix_available():
    matrix={"P1":{"A":1,"B":1,"C":0},"P2":{"A":1,"B":0,"C":1},"P3":{"A":0,"B":1,"C":1}}
    out=run_ablations(candidates(),WEIGHTS,matrix=matrix,k=2)
    full=next(x for x in out if x["ablation"]=="full_wgr_cdp")
    no_opt=next(x for x in out if x["ablation"]=="without_complementary_optimization")
    assert full["selection_method"]=="Available"
    assert full["coverage"]>=no_opt["coverage"]

def test_ablation_fields_are_explicit():
    out=run_ablations(candidates(),WEIGHTS,matrix=None,k=2)
    names={x["ablation"] for x in out}
    assert "without_detectability" in names
    assert "without_blood_background" in names
    assert "without_early_stage" in names
    assert "without_specificity" in names

def test_bootstrap_is_reproducible():
    a=bootstrap_rank_stability(candidates(),WEIGHTS,n_bootstrap=50,k=2,seed=7)
    b=bootstrap_rank_stability(candidates(),WEIGHTS,n_bootstrap=50,k=2,seed=7)
    assert a==b
    assert a["status"]=="Available"

def test_holdout_revalidation_does_not_claim_predictive_performance():
    result=evaluate_selected_candidates(["A","B"],[{"feature":"A"},{"feature":"C"}])
    assert result["revalidated_n"]==1
    assert result["revalidation_rate"]==0.5

def test_complete_a6_record():
    matrix={"P1":{"A":1,"B":0},"P2":{"A":0,"B":1}}
    result=run_a6(candidates(),WEIGHTS,matrix=matrix,k=2,n_bootstrap=25)
    assert result["status"]=="Available"
    assert "baseline_comparison" in result
    assert len(result["ablations"])==8
    assert result["bootstrap_stability"]["n_bootstrap"]==25
    assert len(result["selected"])==2
    assert result["baseline_models"]["logistic"]["status"] == "Data unavailable"
    assert result["baseline_models"]["elastic_net"]["status"] == "Data unavailable"


def test_logistic_and_elastic_net_baselines_require_labels():
    assert logistic_baseline(candidates())["status"] == "Data unavailable"
    assert elastic_net_coordinate_descent(candidates())["status"] == "Data unavailable"


def test_logistic_and_elastic_net_baselines_are_executable_with_labels():
    rows = candidates()
    labels = [1, 1, 0]
    logistic = logistic_baseline(rows, labels=labels, k=2)
    elastic = elastic_net_coordinate_descent(rows, labels=labels, k=2)
    assert logistic["status"] == "Available"
    assert elastic["status"] == "Available"
    assert len(logistic["selected"]) == 2
    assert len(elastic["selected"]) == 2


def test_baselines_do_not_treat_missing_features_as_zero():
    rows = candidates()
    rows[0]["missing_feature"] = None
    rows[1]["missing_feature"] = "Data unavailable"
    rows[2]["missing_feature"] = 1.0
    labels = [1, 1, 0]
    logistic = logistic_baseline(rows, labels=labels, k=2)
    elastic = elastic_net_coordinate_descent(rows, labels=labels, k=2)
    assert logistic["status"] == "Available"
    assert elastic["status"] == "Available"
    assert "missing_feature" in logistic["features"]
    assert "missing_feature" in elastic["features"]


def test_baselines_reject_invalid_or_one_class_labels():
    rows = candidates()
    assert logistic_baseline(rows, labels=[1, 1, 2])["status"] == "Data unavailable"
    assert elastic_net_coordinate_descent(rows, labels=[0, 0, 0])["status"] == "Data unavailable"


def test_baseline_parameters_are_validated():
    rows = candidates()
    labels = [1, 1, 0]
    assert logistic_baseline(rows, labels=labels, learning_rate=0)["status"] == "Data unavailable"
    assert elastic_net_coordinate_descent(rows, labels=labels, l1_ratio=2)["status"] == "Data unavailable"


def test_complete_a6_record_integrates_labelled_baselines():
    result = run_a6(candidates(), WEIGHTS, k=2, n_bootstrap=5, labels=[1, 1, 0])
    assert result["baseline_models"]["logistic"]["status"] == "Available"
    assert result["baseline_models"]["elastic_net"]["status"] == "Available"


def test_ablation_comparison_reports_descriptive_delta_only():
    from wgr_cdp.research.ablation import compare
    rows = run_ablations(candidates(), WEIGHTS, matrix={"P1":{"A":1,"B":0},"P2":{"A":0,"B":1}}, k=2)
    out = compare({r["ablation"]: r for r in rows})
    assert out["status"] == "Available"
    full = next(r for r in out["ablations"] if r["ablation"] == "full_wgr_cdp")
    assert full["coverage_delta_vs_full"] == 0.0


def test_ablation_missing_coverage_does_not_become_zero():
    from wgr_cdp.research.ablation import compare
    rows = run_ablations(candidates(), WEIGHTS, matrix=None, k=2)
    out = compare({r["ablation"]: r for r in rows})
    assert all(r["coverage"] == "Data unavailable" for r in out["ablations"])
    assert all(r["coverage_delta_vs_full"] == "Data unavailable" for r in out["ablations"])


def test_bootstrap_zero_is_unavailable_not_division_by_zero():
    assert bootstrap_rank_stability(candidates(), WEIGHTS, n_bootstrap=0)["status"] == "Data unavailable"


def test_ablation_k_is_capped_at_fifteen():
    rows = run_ablations(candidates(), WEIGHTS, k=100)
    assert all(row["k"] <= 15 for row in rows)
