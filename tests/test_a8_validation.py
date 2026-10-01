from pathlib import Path
import json

from wgr_cdp.research.a8_validation import (
    audit_cohort_leakage,
    audit_candidate_table_leakage,
    validate_state_transition,
    revalidate_selected,
    generalization_summary,
    bootstrap_validation_revalidation,
    build_quality_gate,
    run_a8,
    write_a8_artifacts,
)


def discovery():
    return [
        {"sample_id": "D1", "feature": "A", "effect_size": 0.4, "p_value": 0.01, "q_value": 0.02},
        {"sample_id": "D2", "feature": "B", "effect_size": -0.3, "p_value": 0.02, "q_value": 0.04},
        {"sample_id": "D3", "feature": "C", "effect_size": 0.2, "p_value": 0.1, "q_value": 0.2},
    ]


def validation():
    return [
        {"sample_id": "V1", "feature": "A", "effect_size": 0.3, "p_value": 0.03, "q_value": 0.05},
        {"sample_id": "V2", "feature": "B", "effect_size": -0.1, "p_value": 0.2, "q_value": 0.3},
        {"sample_id": "V3", "feature": "D", "effect_size": 0.4, "p_value": 0.02, "q_value": 0.04},
    ]


def test_leakage_audit_detects_sample_overlap():
    result = audit_cohort_leakage(["D1", "D2"], ["V1", "D2"])
    assert result["status"] == "FAIL"
    assert result["leakage_free"] is False
    assert result["overlap_ids"] == ["D2"]


def test_candidate_overlap_is_not_automatically_leakage():
    result = audit_candidate_table_leakage(discovery(), validation())
    assert result["status"] == "Available"
    assert result["leakage_free"] is True


def test_state_transition_is_explicit():
    result = validate_state_transition()
    assert result["valid_transition"] is True
    assert result["validation"] == "VALIDATION"


def test_revalidation_preserves_missing_candidates():
    result = revalidate_selected(["A", "B", "C"], validation())
    assert result["status"] == "Available"
    assert result["revalidated_n"] == 2
    assert result["revalidation_rate"] == 2 / 3


def test_generalization_reports_direction_without_calling_clinical_performance():
    result = generalization_summary(discovery(), validation(), ["A", "B"])
    assert result["status"] == "Available"
    assert result["candidate_n"] == 2
    assert result["effect_direction_concordance"] == 1.0


def test_bootstrap_is_reproducible():
    a = bootstrap_validation_revalidation(["A", "B"], validation(), 40, 7)
    b = bootstrap_validation_revalidation(["A", "B"], validation(), 40, 7)
    assert a == b
    assert a["status"] == "Available"


def test_quality_gate_is_conditional_without_independent_validation():
    gate = build_quality_gate(
        {"status": "Data unavailable", "leakage_free": None},
        False,
        {"status": "Data unavailable"},
        {"status": "Data unavailable"},
        validate_state_transition(),
    )
    assert gate["overall"] == "CONDITIONAL"


def test_quality_gate_fails_on_leakage():
    gate = build_quality_gate(
        {"status": "FAIL", "leakage_free": False},
        True,
        {"status": "Available"},
        {"status": "Available"},
        validate_state_transition(),
    )
    assert gate["overall"] == "FAIL"


def test_run_a8_with_real_validation_inputs():
    result = run_a8(
        ["A", "B"],
        discovery_rows=discovery(),
        validation_rows=validation(),
        n_bootstrap=25,
    )
    assert result["status"] == "Available"
    assert result["quality_gate"]["overall"] == "PASS"
    assert result["leakage_audit"]["leakage_free"] is True
    assert result["revalidation"]["revalidated_n"] == 2


def test_run_a8_without_validation_is_data_unavailable():
    result = run_a8(["A"], discovery_rows=discovery(), validation_rows=None)
    assert result["status"] == "Data unavailable"
    assert result["quality_gate"]["overall"] == "CONDITIONAL"
    assert result["revalidation"]["status"] == "Data unavailable"


def test_artifacts_are_machine_readable(tmp_path):
    result = run_a8(["A", "B"], discovery_rows=discovery(), validation_rows=validation(), n_bootstrap=5)
    paths = write_a8_artifacts(tmp_path, result)
    assert len(paths["artifacts"]) == 6
    for name in paths["artifacts"]:
        assert (Path(tmp_path) / name).exists()
    payload = json.loads((Path(tmp_path) / "a8_quality_gate.json").read_text(encoding="utf-8"))
    assert payload["overall"] == "PASS"
