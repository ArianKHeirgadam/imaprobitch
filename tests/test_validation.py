from pathlib import Path
import json
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


from wgr_cdp.research.validation import (
    patient_level_split,
    audit_three_way_split,
    stratified_patient_level_split,
    build_split_manifest,
    write_split_manifest,
    evaluate_binary_predictions,
    fit_binary_threshold,
    evaluate_with_frozen_threshold,
)


def test_stratified_split_is_patient_level_and_deterministic():
    rows = (
        [{"patient_id": f"C{i}", "label": "positive"} for i in range(10)]
        + [{"patient_id": f"H{i}", "label": "negative"} for i in range(10)]
        + [{"patient_id": "U1", "label": "unknown"}]
    )
    first = stratified_patient_level_split(rows, .2, .2, 19)
    second = stratified_patient_level_split(rows, .2, .2, 19)
    assert first == second
    assert first["stratified"] is True
    assert first["unknown_label_patients"] == 1
    assert first["audit"]["leakage_free"] is True


def test_split_manifest_is_auditable(tmp_path):
    split = patient_level_split([f"P{i}" for i in range(10)], .2, .2, 3)
    manifest = build_split_manifest(
        split, seed=3, validation_fraction=.2, test_fraction=.2
    )
    assert manifest["schema_version"] == "c04.split-manifest.v1"
    assert manifest["unit"] == "patient"
    assert manifest["leakage_audit"]["leakage_free"] is True
    path = write_split_manifest(tmp_path / "split_manifest.json", manifest)
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    assert loaded == manifest


def test_leakage_audit_fails_on_patient_overlap():
    result = audit_three_way_split(["P1"], ["P1"], ["P2"])
    assert result["status"] == "FAIL"
    assert result["leakage_free"] is False
    assert result["overlaps"]["discovery__validation"] == ["P1"]


def test_missing_labels_are_not_negative_evidence():
    rows = [
        {"patient_id": "P1", "label": "positive", "score": .9},
        {"patient_id": "P2", "label": "unknown", "score": .1},
        {"patient_id": "P3", "score": .2},
        {"patient_id": "P4", "label": "negative", "score": .1},
    ]
    result = evaluate_binary_predictions(rows)
    assert result["status"] == "Available"
    assert result["n_observed"] == 2
    assert result["n_excluded"] == 2
    assert result["positive_n"] == 1
    assert result["negative_n"] == 1
    assert result["confusion_matrix"] == {"tp": 1, "tn": 1, "fp": 0, "fn": 0}


def test_evaluation_is_unavailable_without_both_classes():
    rows = [{"patient_id": "P1", "label": "positive", "score": .9}]
    result = evaluate_binary_predictions(rows)
    assert result["status"] == "Available"
    assert result["metrics"]["roc_auc"] is None
    assert result["metrics"]["specificity"] is None


def test_threshold_is_fit_on_discovery_and_frozen_for_holdout():
    discovery = [
        {"patient_id": "D1", "label": "positive", "score": .9},
        {"patient_id": "D2", "label": "negative", "score": .1},
        {"patient_id": "D3", "label": "positive", "score": .8},
        {"patient_id": "D4", "label": "negative", "score": .2},
    ]
    validation = [
        {"patient_id": "V1", "label": "positive", "score": .7},
        {"patient_id": "V2", "label": "negative", "score": .6},
    ]
    fitted = fit_binary_threshold(discovery)
    assert fitted["status"] == "Available"
    evaluated = evaluate_with_frozen_threshold(validation, fitted)
    assert evaluated["threshold"] == fitted["threshold"]
    assert evaluated["confusion_matrix"] == {"tp": 1, "tn": 0, "fp": 1, "fn": 0}


def test_duplicate_patient_predictions_do_not_get_double_counted():
    rows = [
        {"patient_id": "P1", "label": "positive", "score": .9},
        {"patient_id": "P1", "label": "positive", "score": .8},
    ]
    result = evaluate_binary_predictions(rows)
    assert result["status"] == "Data unavailable"
    assert "duplicate_patient_predictions" in result["reason"]


from wgr_cdp.research.validation import run_c04_evaluation


def test_c04_evaluation_rejects_cross_partition_patient_leakage():
    result = run_c04_evaluation(
        [{"patient_id": "P1", "label": "positive", "score": .9}],
        [{"patient_id": "P1", "label": "positive", "score": .8}],
        [{"patient_id": "P2", "label": "negative", "score": .1}],
    )
    assert result["status"] == "FAIL"
    assert result["leakage_free"] is False
    assert result["overlaps"]["discovery__validation"] == ["P1"]


def test_c04_evaluation_freezes_discovery_threshold():
    discovery = [
        {"patient_id": "D1", "label": "positive", "score": .9},
        {"patient_id": "D2", "label": "negative", "score": .1},
        {"patient_id": "D3", "label": "positive", "score": .8},
        {"patient_id": "D4", "label": "negative", "score": .2},
    ]
    validation = [
        {"patient_id": "V1", "label": "positive", "score": .7},
        {"patient_id": "V2", "label": "negative", "score": .6},
    ]
    test = [
        {"patient_id": "T1", "label": "positive", "score": .75},
        {"patient_id": "T2", "label": "negative", "score": .05},
    ]
    result = run_c04_evaluation(discovery, validation, test)
    assert result["status"] == "Available"
    assert result["threshold_fit"]["status"] == "Available"
    assert result["validation"]["threshold"] == result["threshold_fit"]["threshold"]
    assert result["test"]["threshold"] == result["threshold_fit"]["threshold"]
