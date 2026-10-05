"""End-to-end candidate evidence integration with the C-12 prioritization layer.

A5 remains the canonical evidence table. C-12 adds liquid-biopsy suitability,
patient coverage, explicit external-evidence typing and evidence-strength
confidence without replacing the existing missingness-aware scoring contract.
"""
from __future__ import annotations
import csv, json
from pathlib import Path
from .evidence import normalize_evidence, rank_candidates
from .literature_whitespace import (
    build_candidate_literature_records,
    summarize_whitespace,
    write_literature_evidence,
)
from .sensitivity_analysis import weight_sensitivity, selection_stability, normalize_weights
from .cfdna_prioritization import augment_candidate
from .external_evidence import classify_external_evidence, evidence_hierarchy
from .confidence import evidence_strength_confidence

DEFAULT_WEIGHTS = {
    "biological_evidence": 1.0,
    "statistical_strength": 1.0,
    "detectability": 1.0,
    "blood_background_safety": 1.0,
    "early_stage_score": 1.0,
    "specificity_score": 1.0,
    "literature_novelty": 1.0,
    "literature_validation_gap": 1.0,
    "literature_diagnostic_utility": 1.0,
    "recurrence_prevalence": 1.0,
    "cfdna_suitability": 1.0,
    "patient_coverage": 1.0,
    "external_cancer_evidence": 1.0,
}


def _float_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _candidate_id(row):
    return str(row.get("feature") or row.get("candidate_id") or row.get("candidate") or "")


def _base_evidence(row, matrix=None):
    p = _float_or_none(row.get("p_value"))
    q = _float_or_none(row.get("q_value"))
    statistical = None if q is None else max(0.0, min(1.0, 1.0 - q))
    functional = row.get("functional_evidence")
    biological = None
    if isinstance(functional, dict) and any(functional.get(k) for k in ("gene", "consequence", "impact")):
        biological = _float_or_none(row.get("evidence_score"))
        if biological is not None:
            biological = max(0.0, min(1.0, biological / 100.0))
    evidence = {
        "candidate_id": _candidate_id(row),
        "feature": row.get("feature"),
        "gene": row.get("gene"),
        "candidate_type": row.get("candidate_type") or row.get("variant_type") or "",
        "p_value": p,
        "q_value": q,
        "biological_evidence": biological if biological is not None else "Data unavailable",
        "statistical_strength": statistical if statistical is not None else "Data unavailable",
        "detectability": row.get("detectability", "Data unavailable"),
        "blood_background_safety": row.get("blood_background_safety", "Data unavailable"),
        "early_stage_score": row.get("early_stage_score", "Data unavailable"),
        "specificity_score": row.get("specificity_score", "Data unavailable"),
        "literature": row.get("literature") or {},
        "constraints": row.get("constraints") or {"assay_ok": True, "fpr_ok": True},
    }
    evidence = augment_candidate(evidence, matrix=matrix)
    evidence["external_evidence"] = classify_external_evidence(row)
    evidence["external_cancer_evidence"] = row.get("cancer_evidence_score", "Data unavailable")
    return evidence


def write_a5_artifacts(
    output_dir,
    candidates,
    weights=None,
    constraints=None,
    literature_search=False,
    sensitivity_scenarios=None,
    matrix=None,
    presence_matrix=None,
):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = [_base_evidence(r, matrix=presence_matrix if presence_matrix is not None else matrix) for r in candidates]

    literature_records = build_candidate_literature_records(
        rows,
        search=literature_search,
        sources=("PubMed", "Europe PMC"),
    )
    literature_summary = summarize_whitespace(literature_records)
    for row in rows:
        key = str(row.get("candidate_id") or row.get("feature") or row.get("candidate") or "")
        if key and key in literature_summary:
            row["literature"] = literature_summary[key]

    c10 = write_literature_evidence(
        output,
        rows,
        search=literature_search,
        sources=("PubMed", "Europe PMC"),
        records=literature_records,
    )

    weights = dict(weights or DEFAULT_WEIGHTS)
    ranking = rank_candidates(rows, weights, constraints or {})
    fields = [
        "candidate_id", "feature", "gene", "candidate_type", "p_value", "q_value",
        "biological_evidence", "statistical_strength", "detectability",
        "recurrence_prevalence", "cfdna_suitability", "patient_coverage",
        "external_cancer_evidence", "blood_background_safety",
        "early_stage_score", "specificity_score", "literature_novelty",
        "literature_validation_gap", "literature_diagnostic_utility",
        "research_score", "confidence", "score_status", "score_fields",
    ]
    with (output / "candidate_evidence.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in ranking["ranked"] + ranking["ineligible"] + ranking["unscored"]:
            writer.writerow(row)

    (output / "candidate_constraints.json").write_text(
        json.dumps({
            "constraints": constraints or {},
            "ranked": len(ranking["ranked"]),
            "ineligible": len(ranking["ineligible"]),
            "unscored": len(ranking["unscored"]),
        }, indent=2),
        encoding="utf-8",
    )

    hierarchy = evidence_hierarchy()
    (output / "c12_evidence_hierarchy.json").write_text(
        json.dumps(hierarchy, indent=2, default=str), encoding="utf-8"
    )
    (output / "literature_whitespace.json").write_text(
        json.dumps({
            "schema_version": "c10.literature.v1",
            "searched": bool(literature_search),
            "records": literature_records,
            "summary": literature_summary,
        }, indent=2),
        encoding="utf-8",
    )

    scenarios = sensitivity_scenarios or [
        ("balanced", {}),
        ("detectability_heavy", {"detectability": 2.0}),
        ("cfDNA_heavy", {"cfdna_suitability": 2.0}),
        ("coverage_heavy", {"patient_coverage": 2.0}),
        ("statistical_heavy", {"statistical_strength": 2.0}),
        ("specificity_heavy", {"specificity_score": 2.0}),
    ]
    sensitivity = weight_sensitivity(
        rows, weights, scenarios, constraints or {}
    )
    stability = selection_stability(sensitivity)
    (output / "ranking_sensitivity.json").write_text(
        json.dumps({"results": sensitivity, "stability": stability}, indent=2),
        encoding="utf-8",
    )

    confidence_stability = stability.get("top_k_pairwise_jaccard_mean")
    confidence_rows = []
    for row in ranking["ranked"]:
        confidence = evidence_strength_confidence(
            row,
            stability=confidence_stability,
            validation_status=row.get("validation_status"),
        )
        item = {
            "candidate_id": row.get("candidate_id") or row.get("feature"),
            "research_score": row.get("research_score", "Data unavailable"),
            "confidence": confidence["level"],
            "observed_component_count": confidence["observed_component_count"],
            "observed_components": "|".join(confidence["observed_components"]),
            "stability": confidence["stability"],
            "rationale": confidence["rationale"],
        }
        confidence_rows.append(item)
        row["confidence"] = confidence["level"]
        row["confidence_basis"] = confidence["rationale"]

    with (output / "c12_confidence.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["candidate_id", "research_score", "confidence",
                        "observed_component_count", "observed_components",
                        "stability", "rationale"],
        )
        writer.writeheader()
        writer.writerows(confidence_rows)

    (output / "c12_candidate_prioritization.json").write_text(
        json.dumps({
            "schema_version": "c12.candidate_prioritization.v1",
            "formula": "weighted_mean_of_available_normalized_evidence_components",
            "weights": normalize_weights(weights),
            "ranking": [
                {
                    "candidate_id": row.get("candidate_id"),
                    "research_score": row.get("research_score"),
                    "score_fields": row.get("score_fields"),
                    "cfdna_suitability": row.get("cfdna_suitability"),
                    "patient_coverage": row.get("patient_coverage"),
                    "recurrence_prevalence": row.get("recurrence_prevalence"),
                    "confidence": row.get("confidence"),
                }
                for row in ranking["ranked"]
            ],
            "scientific_boundary": (
                "Scores and confidence are computational prioritization signals. "
                "They are not disease probabilities or clinical diagnostic outputs."
            ),
        }, indent=2, default=str),
        encoding="utf-8",
    )

    return {
        "candidate_evidence": str(output / "candidate_evidence.csv"),
        "candidate_constraints": str(output / "candidate_constraints.json"),
        "literature_whitespace": str(output / "literature_whitespace.json"),
        "c10_literature_evidence_json": c10["json"],
        "c10_literature_evidence_csv": c10["csv"],
        "ranking_sensitivity": str(output / "ranking_sensitivity.json"),
        "c12_evidence_hierarchy": str(output / "c12_evidence_hierarchy.json"),
        "c12_candidate_prioritization": str(output / "c12_candidate_prioritization.json"),
        "c12_confidence": str(output / "c12_confidence.csv"),
        "ranked_count": len(ranking["ranked"]),
        "ineligible_count": len(ranking["ineligible"]),
        "unscored_count": len(ranking["unscored"]),
        "c10": c10,
    }


def append_a5_to_report(output_dir, a5_result):
    report = Path(output_dir) / "report.html"
    if not report.exists():
        return False
    import html
    document = report.read_text(encoding="utf-8")
    section = (
        "<hr><h2>Phase A5/C-12 Candidate Prioritization</h2>"
        "<p>Research prioritization combines observed statistical, recurrence, "
        "cfDNA-suitability, external-evidence and coverage components; unavailable "
        "components are not treated as negative evidence.</p>"
        "<ul>"
        f"<li>Eligible ranked candidates: {int(a5_result.get('ranked_count', 0))}</li>"
        f"<li>Hard-constraint ineligible candidates: {int(a5_result.get('ineligible_count', 0))}</li>"
        f"<li>Unscored candidates: {int(a5_result.get('unscored_count', 0))}</li>"
        "</ul>"
        "<p>Artifacts: <code>candidate_evidence.csv</code>, "
        "<code>c12_candidate_prioritization.json</code>, <code>c12_evidence_hierarchy.json</code>, "
        "<code>c12_confidence.csv</code>, <code>ranking_sensitivity.json</code>.</p>"
        "<p>C-10: <code>c10_literature_evidence.json</code>, "
        "<code>c10_literature_evidence.csv</code>.</p>"
    )
    marker = "</body>"
    document = document.replace(marker, section + marker, 1) if marker in document else document + section
    report.write_text(document, encoding="utf-8")
    return True
