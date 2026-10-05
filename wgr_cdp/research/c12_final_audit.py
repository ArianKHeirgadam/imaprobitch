"""C-12.7: final scientific and reproducibility audit.

C-12 is the terminal hardening layer. It verifies the new liquid-biopsy
prioritization, patient-presence coverage, statistical-method, cohort-design,
evidence-hierarchy and confidence contracts, then records the remaining
data-dependent scientific conditions explicitly.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

UNAVAILABLE = "Data unavailable"
SCHEMA_VERSION = "c12.final_audit.v1"


def _nonempty(path):
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _csv_headers(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(next(csv.reader(handle), []))


def audit_c12(output_dir, config=None, run_id=None):
    root = Path(output_dir)
    checks = []

    def check(name, passed, detail):
        checks.append({
            "check": name,
            "status": "PASS" if passed else "FAIL",
            "detail": detail,
        })

    required = [
        "candidate_evidence.csv",
        "c12_candidate_prioritization.json",
        "c12_evidence_hierarchy.json",
        "c12_confidence.csv",
        "c12_cohort_design.json",
        "c12_validation_coverage.json",
    ]
    required_ok = all(_nonempty(root / rel) for rel in required)
    check(
        "c12_required_artifacts",
        required_ok,
        "All mandatory C-12 artifacts are present and non-empty."
        if required_ok else
        "One or more mandatory C-12 artifacts are missing or empty.",
    )

    # C-11 is the immediate upstream integration gate.
    try:
        c11 = _json(root / "c11_integration_manifest.json")
        check(
            "c11_upstream_gate",
            c11.get("schema_version") == "c11.integration.v1"
            and c11.get("status") == "PASS",
            f"schema={c11.get('schema_version')}; status={c11.get('status')}",
        )
    except Exception as exc:
        check("c11_upstream_gate", False, f"C-11 manifest unreadable: {type(exc).__name__}")

    headers = _csv_headers(root / "candidate_evidence.csv")
    score_fields = {
        "recurrence_prevalence",
        "cfdna_suitability",
        "patient_coverage",
        "external_cancer_evidence",
        "research_score",
        "score_fields",
    }
    check(
        "candidate_score_schema",
        score_fields <= set(headers),
        "Candidate evidence exposes the formal C-12 score components."
        if score_fields <= set(headers) else
        "Candidate evidence is missing one or more C-12 score components.",
    )

    try:
        panel = _json(root / "c12_candidate_prioritization.json")
        formula_ok = panel.get("formula") == "weighted_mean_of_available_normalized_evidence_components"
        weight_map = panel.get("weights", {})
        weight_ok = bool(weight_map) and abs(sum(float(v) for v in weight_map.values()) - 1.0) < 1e-9
        check(
            "formal_score_formula",
            formula_ok and weight_ok,
            f"formula_ok={formula_ok}; normalized_weight_sum={sum(float(v) for v in weight_map.values()) if weight_map else 0.0:.6g}",
        )
    except Exception as exc:
        check("formal_score_formula", False, f"artifact unreadable: {type(exc).__name__}")

    try:
        hierarchy = _json(root / "c12_evidence_hierarchy.json")
        categories = {item.get("category") for item in hierarchy.get("tiers", [])}
        required_categories = {"functional", "population_identity", "clinical", "cancer_specific", "cfDNA_specific"}
        check(
            "evidence_hierarchy",
            required_categories <= categories,
            f"categories={sorted(categories)}",
        )
    except Exception as exc:
        check("evidence_hierarchy", False, f"artifact unreadable: {type(exc).__name__}")

    try:
        confidence_headers = set(_csv_headers(root / "c12_confidence.csv"))
        confidence_ok = {"candidate_id", "research_score", "confidence", "rationale"} <= confidence_headers
        check("confidence_contract", confidence_ok, f"headers={sorted(confidence_headers)}")
    except Exception as exc:
        check("confidence_contract", False, f"artifact unreadable: {type(exc).__name__}")

    try:
        coverage = _json(root / "c12_validation_coverage.json")
        valid_status = coverage.get("status") in {"Available", UNAVAILABLE}
        check(
            "frozen_panel_validation_contract",
            valid_status and coverage.get("reoptimized") is False,
            f"status={coverage.get('status')}; reoptimized={coverage.get('reoptimized')}",
        )
    except Exception as exc:
        check("frozen_panel_validation_contract", False, f"artifact unreadable: {type(exc).__name__}")

    try:
        cohort = _json(root / "c12_cohort_design.json")
        check(
            "cohort_design_contract",
            cohort.get("schema_version") == "c12.cohort_design.v1"
            and cohort.get("status") in {"Available", UNAVAILABLE, "REVIEW"},
            f"schema={cohort.get('schema_version')}; status={cohort.get('status')}",
        )
    except Exception as exc:
        check("cohort_design_contract", False, f"artifact unreadable: {type(exc).__name__}")

    multimodal_requested = bool((config or {}).get("features"))
    presence_available = _nonempty(
        root / "multimodal" / "patient_candidate_presence_matrix.csv"
    )
    check(
        "patient_presence_matrix",
        presence_available if multimodal_requested else True,
        "Explicit patient presence matrix is available."
        if presence_available else
        ("Data unavailable because no multimodal feature table was supplied."
         if not multimodal_requested else
         "Multimodal analysis was requested but the patient presence matrix is missing."),
    )

    fail_count = sum(item["status"] == "FAIL" for item in checks)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if fail_count == 0 else "FAIL",
        "run_id": str(run_id or UNAVAILABLE),
        "checks": checks,
        "remaining_scientific_conditions": [
            "Real cfDNA/plasma observations are required before claiming assay detectability.",
            "Independent validation coverage is Data unavailable when no independent patient-level validation matrix is supplied.",
            "Cohort metadata must be supplied and reviewed before interpreting potential batch/confounding flags.",
            "Literature novelty, validation gap and diagnostic utility remain Data unavailable until manual review.",
        ],
        "scientific_boundary": (
            "C-12 PASS establishes implementation and audit completeness. "
            "It is not a clinical validation, diagnostic performance, or disease-probability claim."
        ),
    }


def write_c12_final_audit(output_dir, config=None, run_id=None):
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    result = audit_c12(root, config=config, run_id=run_id)
    path = root / "c12_final_audit.json"
    path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return {
        "status": result["status"],
        "schema_version": SCHEMA_VERSION,
        "audit": str(path),
        "failed_checks": sum(item["status"] == "FAIL" for item in result["checks"]),
    }


def append_c12_final_audit(output_dir, result):
    report = Path(output_dir) / "report.html"
    if not report.exists():
        return False
    import html
    section = (
        "<hr><h2>C-12 Final Scientific Audit</h2>"
        "<p>C-12 is the terminal implementation/reproducibility hardening layer. "
        "Confidence means strength of computational evidence, not disease probability.</p>"
        f"<ul><li>Audit status: <strong>{html.escape(str(result.get('status', UNAVAILABLE)))}</strong></li>"
        f"<li>Failed software checks: {int(result.get('failed_checks', 0))}</li></ul>"
        "<p>Final machine-readable artifact: <code>c12_final_audit.json</code>.</p>"
    )
    document = report.read_text(encoding="utf-8")
    marker = "</body>"
    document = document.replace(marker, section + marker, 1) if marker in document else document + section
    report.write_text(document, encoding="utf-8")
    return True
