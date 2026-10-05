from pathlib import Path
import json

import pytest

from wgr_cdp.research.robustness import (
    k_sensitivity,
    missingness_stress,
    run_c09_robustness,
    threshold_sensitivity,
    weight_sensitivity,
    write_c09_artifacts,
)
from wgr_cdp.research.sensitivity_analysis import normalize_weights


WEIGHTS = {
    "biological_evidence": 1.0,
    "statistical_strength": 1.0,
    "detectability": 1.0,
    "blood_background_safety": 1.0,
    "early_stage_score": 1.0,
    "specificity_score": 1.0,
    "literature_novelty": 1.0,
    "literature_validation_gap": 1.0,
    "literature_diagnostic_utility": 1.0,
}


def candidates():
    return [
        {
            "candidate_id": "A",
            "detectability": 0.95,
            "blood_background_safety": 0.95,
            "early_stage_score": 0.80,
            "specificity_score": 0.90,
            "statistical_strength": 0.95,
            "biological_evidence": 0.80,
        },
        {
            "candidate_id": "B",
            "detectability": 0.60,
            "blood_background_safety": 0.80,
            "early_stage_score": 0.55,
            "specificity_score": 0.95,
            "statistical_strength": 0.80,
            "biological_evidence": 0.75,
        },
        {
            "candidate_id": "C",
            "detectability": 0.45,
            "blood_background_safety": 0.99,
            "early_stage_score": 0.90,
            "specificity_score": 0.70,
            "statistical_strength": 0.70,
            "biological_evidence": 0.70,
        },
    ]


def test_normalize_weights_rejects_nonfinite_and_negative():
    with pytest.raises(ValueError):
        normalize_weights({"detectability": float("nan")})
    with pytest.raises(ValueError):
        normalize_weights({"detectability": float("inf")})
    with pytest.raises(ValueError):
        normalize_weights({"detectability": -1})
    with pytest.raises(ValueError, match="Unknown evidence weight field"):
        normalize_weights({"unknown_component": 1.0})


def test_weight_sensitivity_is_deterministic_and_auditable():
    scenarios = [
        ("baseline", {}),
        ("detectability_2x", {"detectability": 2.0}),
    ]
    first = weight_sensitivity(candidates(), WEIGHTS, scenarios)
    second = weight_sensitivity(candidates(), WEIGHTS, scenarios)
    assert first == second
    assert first[0]["ranked_count"] == 3
    assert first[1]["scenario"] == "detectability_2x"


def test_threshold_sensitivity_applies_hard_constraints_before_ranking():
    rows = candidates()
    result = threshold_sensitivity(
        rows,
        WEIGHTS,
        detectability_thresholds=(0.0, 0.75),
        background_thresholds=(1.0, 0.1),
    )
    strict = next(r for r in result if r["min_detectability"] == 0.75 and r["max_background"] == 0.1)
    assert strict["ranked_count"] <= 1
    assert strict["ineligible_count"] >= 2


def test_threshold_sensitivity_invalid_threshold_rejected():
    with pytest.raises(ValueError):
        threshold_sensitivity(candidates(), WEIGHTS, (-0.1,), (1.0,))


def test_k_sensitivity_preserves_missing_cells():
    matrix = {
        "P1": {"A": 1.0, "B": 0.0},
        "P2": {"A": 0.0},
        "P3": {"B": 1.0},
    }
    result = k_sensitivity(matrix, k_values=(1, 2), min_gain=0.0)
    assert result["status"] == "Available"
    assert result["results"][0]["k"] == 1
    assert all(item["selected_count"] <= item["k"] <= 15 for item in result["results"])


def test_k_sensitivity_missing_matrix_is_unavailable():
    assert k_sensitivity(None)["status"] == "Data unavailable"


def test_k_values_are_capped():
    result = k_sensitivity({"P": {"A": 1.0, "B": 1.0}}, k_values=(100,), min_gain=0.0)
    assert result["results"][0]["k"] <= 15


def test_missingness_stress_is_seed_deterministic_and_explicit():
    kwargs = dict(
        candidates=candidates(),
        base_weights=WEIGHTS,
        missingness_rates=(0.0, 0.5),
        repeats=8,
        seed=7,
        k=2,
    )
    first = missingness_stress(**kwargs)
    second = missingness_stress(**kwargs)
    assert first == second
    assert first["perturbation_model"] == "synthetic_missingness_masking"


def test_missingness_stress_does_not_modify_inputs():
    rows = candidates()
    snapshot = json.loads(json.dumps(rows))
    missingness_stress(rows, WEIGHTS, (0.5,), repeats=3, seed=1)
    assert rows == snapshot


def test_c09_integrated_record_contains_all_axes():
    result = run_c09_robustness(
        candidates(),
        WEIGHTS,
        matrix={"P1": {"A": 1.0, "B": 0.0}, "P2": {"B": 1.0}},
        k_values=(1, 2, 3),
        missingness_repeats=3,
    )
    assert result["status"] == "Available"
    assert result["schema_version"] == "c09.robustness.v1"
    assert result["weight_robustness"]["status"] == "Available"
    assert result["threshold_robustness"]["status"] == "Available"
    assert result["k_sensitivity"]["status"] == "Available"
    assert result["missingness_stress"]["status"] == "Available"


def test_c09_artifacts_are_written(tmp_path: Path):
    result = write_c09_artifacts(
        tmp_path,
        candidates(),
        base_weights=WEIGHTS,
        matrix={"P1": {"A": 1.0, "B": 0.0}, "P2": {"B": 1.0}},
        k_values=(1, 2),
        missingness_repeats=2,
    )
    assert result["status"] == "Available"
    for key, path in result["artifacts"].items():
        assert Path(path).exists(), key
    payload = json.loads((tmp_path / "c09_robustness.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "c09.robustness.v1"


def test_c09_report_append_is_auditable(tmp_path: Path):
    report = tmp_path / "report.html"
    report.write_text("<html><body><h1>Report</h1></body></html>", encoding="utf-8")
    from wgr_cdp.research.robustness import append_c09_to_report
    result = run_c09_robustness(
        candidates(),
        WEIGHTS,
        matrix={"P1": {"A": 1.0}},
        k_values=(1,),
        missingness_repeats=1,
    )
    assert append_c09_to_report(tmp_path, result) is True
    assert "Phase C-09 Robustness" in report.read_text(encoding="utf-8")
