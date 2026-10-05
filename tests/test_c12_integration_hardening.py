from pathlib import Path
import csv
import json

from wgr_cdp.research.a5_integration import write_a5_artifacts
from wgr_cdp.research.a7_final_panel import build_final_panel
from wgr_cdp.cli.main import build_parser
from wgr_cdp.multimodal.engine import analyze_multimodal_features


def _candidate(cid, freq=0.5):
    return {
        "candidate_id": cid,
        "feature": cid,
        "case_frequency": freq,
        "p_value": 0.01,
        "q_value": 0.02,
        "functional_evidence": {"gene": "TP53"},
        "evidence_score": 80,
    }


def test_a5_uses_explicit_presence_for_patient_coverage(tmp_path: Path):
    candidates = [_candidate("A")]
    presence = {"P1": {"A": 1}, "P2": {"A": 0}, "P3": {"A": 1}}
    result = write_a5_artifacts(tmp_path, candidates, literature_search=False,
                                 presence_matrix=presence)
    assert Path(result["c12_candidate_prioritization"]).exists()
    rows = list(csv.DictReader((tmp_path / "candidate_evidence.csv").open(
        encoding="utf-8", newline=""
    )))
    assert rows[0]["patient_coverage"] == str(2 / 3)


def test_a7_presence_objective_can_choose_complementary_candidate():
    candidates = [
        _candidate("A", 0.9),
        _candidate("B", 0.8),
        _candidate("C", 0.7),
    ]
    for row in candidates:
        row.update({
            "biological_evidence": 0.8,
            "statistical_strength": 0.8,
            "detectability": 0.8,
            "blood_background_safety": 0.8,
            "early_stage_score": 0.8,
            "specificity_score": 0.8,
        })
    presence = {
        "P1": {"A": 1, "B": 0, "C": 0},
        "P2": {"A": 1, "B": 0, "C": 0},
        "P3": {"A": 0, "B": 0, "C": 1},
        "P4": {"A": 0, "B": 0, "C": 1},
    }
    result = build_final_panel(candidates, presence_matrix=presence, max_k=2)
    assert result["diagnostics"]["selection_objective"] == "patient_presence"
    assert set(result["panel"]["selected"]) == {"A", "C"}
    assert result["panel"]["presence_coverage"] == 1.0


def test_multimodal_preserves_optional_cfdna_measurements():
    rows = [
        {"patient": "P1", "group": "case", "region": "1:1-2",
         "feature_type": "SNV", "value": "1", "status": "Detected",
         "vaf": "0.30", "ccf": "0.80", "mappability": "0.99"},
        {"patient": "P2", "group": "case", "region": "1:1-2",
         "feature_type": "SNV", "value": "1", "status": "Detected",
         "vaf": "0.20", "ccf": "0.60", "mappability": "0.97"},
        {"patient": "H1", "group": "control", "region": "1:1-2",
         "feature_type": "SNV", "value": "0", "status": "Not detected"},
    ]
    out = analyze_multimodal_features(rows)
    record = out["SNV"][0]
    assert record["allele_fraction"] == 0.25
    assert record["clonality"] == 0.7
    assert record["mappability"] == 0.98


def test_cli_accepts_cohort_metadata():
    args = build_parser().parse_args([
        "run", "--healthy", "h", "--cancer", "c", "--output", "o",
        "--cohort-metadata", "meta.csv",
    ])
    assert args.cohort_metadata == "meta.csv"
