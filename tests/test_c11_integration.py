from pathlib import Path
import json

from wgr_cdp.research.c11_integration import (
    SCHEMA_VERSION,
    audit_run_artifacts,
    build_c11_manifest,
    write_c11_artifacts,
)


REQUIRED = (
    "variants/variants.csv",
    "variants/significant_variants.csv",
    "variants/genes.csv",
    "variants/significant_genes.csv",
    "variants/candidates.csv",
    "variants/summary.json",
    "variants/annotations.json",
    "variants/run.json",
    "report.html",
    "candidate_evidence.csv",
    "candidate_constraints.json",
    "ranking_sensitivity.json",
    "literature_whitespace.json",
    "c10_literature_evidence.json",
    "c10_literature_evidence.csv",
    "a6_validation.json",
    "a6_baseline_comparison.json",
    "a6_bootstrap_stability.json",
    "a6_ablation.csv",
    "final_panel.json",
    "final_panel_candidates.csv",
    "final_panel_constraints.json",
    "final_panel_diagnostics.json",
    "a8_validation.json",
    "a8_leakage_audit.json",
    "a8_bootstrap_stability.json",
    "a8_generalization.json",
    "a8_generalization.csv",
    "a8_quality_gate.json",
    "c09_robustness.json",
    "c09_weight_sensitivity.csv",
    "c09_threshold_sensitivity.csv",
    "c09_k_sensitivity.csv",
    "c09_missingness_stress.csv",
)


def _csv(path, header="id\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header, encoding="utf-8")


def _fixture(root: Path):
    for rel in REQUIRED:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".csv":
            _csv(path)
        else:
            path.write_text("{}", encoding="utf-8")

    (root / "candidate_constraints.json").write_text(
        json.dumps({"ranked": 1, "ineligible": 1, "unscored": 0}),
        encoding="utf-8",
    )
    (root / "candidate_evidence.csv").write_text(
        "candidate_id\nA\nB\n", encoding="utf-8"
    )
    (root / "c10_literature_evidence.json").write_text(
        json.dumps({
            "schema_version": "c10.literature.v1",
            "sources": ["PubMed", "Europe PMC"],
            "records": [{"candidate_id": "A"}],
        }),
        encoding="utf-8",
    )
    (root / "c10_literature_evidence.csv").write_text(
        "candidate_id\nA\n", encoding="utf-8"
    )
    (root / "final_panel.json").write_text(
        json.dumps({"panel": {"selected": ["A"], "max_k": 15}}),
        encoding="utf-8",
    )
    (root / "c09_robustness.json").write_text(
        json.dumps({"schema_version": "c09.robustness.v1"}),
        encoding="utf-8",
    )
    (root / "a8_quality_gate.json").write_text(
        json.dumps({"overall": "CONDITIONAL"}),
        encoding="utf-8",
    )


def test_c11_audits_complete_required_artifacts(tmp_path: Path):
    _fixture(tmp_path)
    result = audit_run_artifacts(tmp_path)
    assert result["status"] == "PASS"
    assert result["artifact_count"] == 34
    assert result["available_artifact_count"] == 34


def test_c11_detects_missing_required_artifact(tmp_path: Path):
    _fixture(tmp_path)
    (tmp_path / "a6_ablation.csv").unlink()
    result = audit_run_artifacts(tmp_path)
    assert result["status"] == "FAIL"


def test_c11_rejects_bad_cross_stage_contract(tmp_path: Path):
    _fixture(tmp_path)
    (tmp_path / "c10_literature_evidence.csv").write_text(
        "candidate_id\nA\nB\n", encoding="utf-8"
    )
    result = audit_run_artifacts(tmp_path)
    checks = {item["check"]: item["status"] for item in result["checks"]}
    assert checks["c10_literature_contract"] == "FAIL"


def test_c11_preserves_conditional_scientific_validation(tmp_path: Path):
    _fixture(tmp_path)
    result = build_c11_manifest(
        tmp_path,
        config={"validation_candidates": None},
        run_id="r1",
    )
    assert result["schema_version"] == SCHEMA_VERSION
    assert result["status"] == "PASS"
    assert result["optional_inputs_observed"]["independent_validation"] is False


def test_c11_writer_creates_machine_readable_artifacts(tmp_path: Path):
    _fixture(tmp_path)
    result = write_c11_artifacts(tmp_path, config={"alpha": 0.05}, run_id="r1")
    assert result["status"] == "PASS"
    assert Path(result["manifest"]).exists()
    assert Path(result["artifact_index"]).exists()
    payload = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
    assert payload["run_id"] == "r1"
    assert payload["dependency_graph"]["a9_reproducibility"] == ["c11_integration"]
