from pathlib import Path

from wgr_cdp.research.a7_final_panel import (
    build_final_panel,
    multimodal_to_candidates,
    write_final_panel,
)

W = {
    "biological_evidence": 1,
    "statistical_strength": 1,
    "detectability": 1,
    "blood_background_safety": 1,
    "early_stage_score": 1,
    "specificity_score": 1,
    "literature_novelty": 1,
    "literature_validation_gap": 1,
    "literature_diagnostic_utility": 1,
}


def candidate(cid, score=0.8):
    return {
        "candidate_id": cid,
        "feature": cid,
        "biological_evidence": score,
        "statistical_strength": score,
        "detectability": score,
        "blood_background_safety": score,
        "early_stage_score": score,
        "specificity_score": score,
    }


def test_multimodal_candidates_preserve_unavailable():
    rows = [{
        "feature": "8:100-200|CNV",
        "feature_type": "CNV",
        "detectability": "",
        "blood_background": "",
        "early_stage_fraction": "0.5",
        "specificity": "0.8",
        "validation_status": "",
    }]
    out = multimodal_to_candidates(rows)
    assert out[0]["detectability"] == "Data unavailable"
    assert out[0]["blood_background_safety"] == "Data unavailable"
    assert out[0]["early_stage_score"] == 0.5


def test_multimodal_mapping_accepts_actual_optional_evidence_aliases():
    rows = [{
        "feature": "1:10-20|SNV",
        "feature_type": "SNV",
        "power": "0.91",
        "blood_background_max": "0.04",
        "early_stage_score": "0.60",
        "specificity_score": "0.88",
        "q_value": "0.01",
        "p_value": "0.001",
    }]
    out = multimodal_to_candidates(rows)[0]
    assert out["detectability"] == 0.91
    assert out["blood_background_safety"] == 0.96
    assert out["early_stage_score"] == 0.60
    assert out["specificity_score"] == 0.88
    assert out["statistical_strength"] == 0.99


def test_final_panel_optimizes_full_eligible_universe_not_ranked_top_k():
    candidates = [candidate("A", .95), candidate("B", .94), candidate("C", .80)]
    matrix = {
        "P1": {"A": .95, "B": .02, "C": .90},
        "P2": {"A": .95, "B": .02, "C": .90},
        "P3": {"A": .02, "B": .95, "C": .90},
        "P4": {"A": .02, "B": .95, "C": .90},
    }
    result = build_final_panel(candidates, matrix, max_k=2, weights=W)
    assert result["status"] == "Available"
    assert result["eligible_candidate_ids"] == ["A", "B", "C"]
    assert result["panel"]["status"] == "Available"
    assert result["panel"]["k"] == 2
    assert set(result["panel"]["selected"]) == {"A", "B"}
    assert 0 <= result["panel"]["coverage"] <= 1
    assert 0 < result["panel"]["alpha_per_feature"] < .05


def test_final_panel_exact_optimization_can_choose_lower_ranked_complement():
    candidates = [candidate("A", .99), candidate("B", .98), candidate("C", .70)]
    matrix = {
        "P1": {"A": 1.0, "B": 0.0, "C": 1.0},
        "P2": {"A": 1.0, "B": 0.0, "C": 1.0},
        "P3": {"A": 0.0, "B": 1.0, "C": 1.0},
        "P4": {"A": 0.0, "B": 1.0, "C": 1.0},
    }
    result = build_final_panel(candidates, matrix, max_k=2, weights=W)
    assert set(result["panel"]["selected"]) == {"A", "B"}
    assert result["panel"]["coverage"] >= 0.99


def test_final_panel_missing_matrix_is_explicit():
    result = build_final_panel([candidate("A")], None, 1, weights=W)
    assert result["panel"]["status"] == "Data unavailable"
    assert result["panel"]["coverage"] == "Data unavailable"
    assert result["panel"]["selected"] == ["A"]


def test_final_panel_applies_hard_detectability_constraint():
    candidates = [candidate("A", .9), candidate("B", .8)]
    candidates[0]["detectability"] = 0.01
    candidates[1]["detectability"] = 0.90
    result = build_final_panel(
        candidates,
        None,
        1,
        weights=W,
        constraints={"min_detectability": 0.5, "max_background": 1.0},
    )
    assert result["eligible_candidate_ids"] == ["B"]
    assert result["ineligible_count"] == 1


def test_final_panel_writes_auditable_artifacts(tmp_path: Path):
    result = write_final_panel(
        tmp_path,
        [candidate("A"), candidate("B", .7)],
        matrix={"P1": {"A": .9, "B": .2}},
        max_k=1,
        weights=W,
    )
    assert result["status"] == "Available"
    assert (tmp_path / "final_panel.json").exists()
    assert (tmp_path / "final_panel_candidates.csv").exists()
    assert (tmp_path / "final_panel_constraints.json").exists()

    text = (tmp_path / "final_panel_candidates.csv").read_text(encoding="utf-8")
    assert "selected" in text.splitlines()[0]
    assert "A" in text
