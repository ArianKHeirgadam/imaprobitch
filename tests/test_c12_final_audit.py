from pathlib import Path
import json

from wgr_cdp.research.c12_final_audit import audit_c12, write_c12_final_audit

REQUIRED = [
    "candidate_evidence.csv",
    "c12_candidate_prioritization.json",
    "c12_evidence_hierarchy.json",
    "c12_confidence.csv",
    "c12_cohort_design.json",
    "c12_validation_coverage.json",
]


def _fixture(root: Path):
    (root / "candidate_evidence.csv").write_text(
        "candidate_id,recurrence_prevalence,cfdna_suitability,patient_coverage,external_cancer_evidence,research_score,score_fields\nA,0.5,0.7,0.8,Data unavailable,0.7,statistical_strength\n",
        encoding="utf-8",
    )
    (root / "c12_candidate_prioritization.json").write_text(
        json.dumps({
            "formula": "weighted_mean_of_available_normalized_evidence_components",
            "weights": {"a": 0.5, "b": 0.5},
        }),
        encoding="utf-8",
    )
    (root / "c12_evidence_hierarchy.json").write_text(
        json.dumps({"schema_version":"c12.evidence_hierarchy.v1","tiers":[
            {"category":"functional"},{"category":"population_identity"},{"category":"clinical"},
            {"category":"cancer_specific"},{"category":"cfDNA_specific"}]}),
        encoding="utf-8",
    )
    (root / "c12_confidence.csv").write_text(
        "candidate_id,research_score,confidence,rationale\nA,0.7,MODERATE,x\n",
        encoding="utf-8",
    )
    (root / "c12_cohort_design.json").write_text(
        json.dumps({"schema_version":"c12.cohort_design.v1","status":"Available"}),
        encoding="utf-8",
    )
    (root / "c12_validation_coverage.json").write_text(
        json.dumps({"status":"Data unavailable","reoptimized":False}),
        encoding="utf-8",
    )


def test_c12_final_audit_passes_complete_contract(tmp_path: Path):
    _fixture(tmp_path)
    result = audit_c12(tmp_path, config={"features": None}, run_id="r1")
    assert result["status"] == "PASS"


def test_c12_final_audit_detects_missing_contract(tmp_path: Path):
    _fixture(tmp_path)
    (tmp_path / "c12_confidence.csv").unlink()
    result = audit_c12(tmp_path, config={"features": None})
    assert result["status"] == "FAIL"


def test_c12_writer(tmp_path: Path):
    _fixture(tmp_path)
    result = write_c12_final_audit(tmp_path, config={"features": None}, run_id="r1")
    assert result["status"] == "PASS"
    assert Path(result["audit"]).exists()
