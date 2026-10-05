"""End-to-end A5 candidate evidence integration.

This module consumes existing discovery/cnv/multimodal outputs and produces one
auditable evidence table. It never invents missing scientific measurements.
"""
from __future__ import annotations
import csv, json
from pathlib import Path
from .evidence import normalize_evidence, rank_candidates
from .literature_whitespace import (
    build_candidate_literature_records,
    literature_record,
    summarize_whitespace,
    write_literature_evidence,
)
from .sensitivity_analysis import weight_sensitivity, selection_stability

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
}

def _float_or_none(value):
    try: return float(value)
    except (TypeError, ValueError): return None

def _candidate_id(row):
    return str(row.get("feature") or row.get("candidate_id") or row.get("candidate") or "")

def _base_evidence(row):
    p=_float_or_none(row.get("p_value")); q=_float_or_none(row.get("q_value"))
    statistical = None if q is None else max(0.0, min(1.0, 1.0-q))
    # Existing discovery evidence is retained as source evidence, but is not
    # relabeled as biological truth unless functional evidence is present.
    functional = row.get("functional_evidence")
    biological = None
    if isinstance(functional, dict) and any(functional.get(k) for k in ("gene","consequence","impact")):
        biological = _float_or_none(row.get("evidence_score"))
        if biological is not None: biological = max(0.0,min(1.0,biological/100.0))
    return {
        "candidate_id": _candidate_id(row),
        "feature": row.get("feature"),
        "gene": row.get("gene"),
        "candidate_type": row.get("candidate_type") or row.get("variant_type") or "",
        "p_value": p, "q_value": q,
        "biological_evidence": biological if biological is not None else "Data unavailable",
        "statistical_strength": statistical if statistical is not None else "Data unavailable",
        "detectability": row.get("detectability", "Data unavailable"),
        "blood_background_safety": row.get("blood_background_safety", "Data unavailable"),
        "early_stage_score": row.get("early_stage_score", "Data unavailable"),
        "specificity_score": row.get("specificity_score", "Data unavailable"),
        "literature": row.get("literature") or {},
        "constraints": row.get("constraints") or {"assay_ok": True, "fpr_ok": True},
    }

def write_a5_artifacts(output_dir, candidates, weights=None, constraints=None,
                       literature_search=False, sensitivity_scenarios=None):
    output=Path(output_dir); output.mkdir(parents=True,exist_ok=True)
    rows=[_base_evidence(r) for r in candidates]
    literature_records = build_candidate_literature_records(
        rows,
        search=literature_search,
        sources=("PubMed", "Europe PMC"),
    )
    literature_summary=summarize_whitespace(literature_records)
    for row in rows:
        key = str(row.get("candidate_id") or row.get("feature") or row.get("candidate") or "")
        if key and key in literature_summary:
            row["literature"]=literature_summary[key]
    c10 = write_literature_evidence(
        output,
        rows,
        search=literature_search,
        sources=("PubMed", "Europe PMC"),
        records=literature_records,
    )
    weights=dict(weights or DEFAULT_WEIGHTS)
    ranking=rank_candidates(rows,weights,constraints or {})
    fields=["candidate_id","feature","gene","candidate_type","p_value","q_value",
            "biological_evidence","statistical_strength","detectability",
            "blood_background_safety","early_stage_score","specificity_score",
            "literature_novelty","literature_validation_gap",
            "literature_diagnostic_utility","research_score","score_status",
            "score_fields"]
    with (output/"candidate_evidence.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,extrasaction="ignore"); w.writeheader()
        for row in ranking["ranked"] + ranking["ineligible"] + ranking["unscored"]:
            w.writerow(row)
    (output/"candidate_constraints.json").write_text(json.dumps(
        {"constraints":constraints or {}, "ranked":len(ranking["ranked"]),
         "ineligible":len(ranking["ineligible"]), "unscored":len(ranking["unscored"])},indent=2
    ),encoding="utf-8")
    (output/"literature_whitespace.json").write_text(json.dumps(
        {"schema_version":"c10.literature.v1","searched":bool(literature_search),"records":literature_records,
         "summary":literature_summary},indent=2
    ),encoding="utf-8")
    scenarios=sensitivity_scenarios or [
        ("balanced", {}),
        ("detectability_heavy", {"detectability": 2.0}),
        ("statistical_heavy", {"statistical_strength": 2.0}),
        ("specificity_heavy", {"specificity_score": 2.0}),
    ]
    sensitivity=weight_sensitivity(rows,weights,scenarios,constraints or {})
    (output/"ranking_sensitivity.json").write_text(json.dumps(
        {"results":sensitivity,"stability":selection_stability(sensitivity)},indent=2
    ),encoding="utf-8")
    return {
        "candidate_evidence":str(output/"candidate_evidence.csv"),
        "candidate_constraints":str(output/"candidate_constraints.json"),
        "literature_whitespace":str(output/"literature_whitespace.json"),
        "c10_literature_evidence_json":c10["json"],
        "c10_literature_evidence_csv":c10["csv"],
        "ranking_sensitivity":str(output/"ranking_sensitivity.json"),
        "ranked_count":len(ranking["ranked"]),
        "ineligible_count":len(ranking["ineligible"]),
        "unscored_count":len(ranking["unscored"]),
    }

def append_a5_to_report(output_dir, a5_result):
    """Add an auditable A5 summary to the existing real-analysis HTML report."""
    report = Path(output_dir) / "report.html"
    if not report.exists():
        return False
    import html
    document = report.read_text(encoding="utf-8")
    section = (
        "<hr><h2>Phase A5 Candidate Evidence</h2>"
        "<p>Evidence integration is research prioritization only; missing measurements remain unavailable.</p>"
        "<ul>"
        f"<li>Eligible ranked candidates: {int(a5_result.get('ranked_count', 0))}</li>"
        f"<li>Hard-constraint ineligible candidates: {int(a5_result.get('ineligible_count', 0))}</li>"
        f"<li>Unscored candidates: {int(a5_result.get('unscored_count', 0))}</li>"
        "</ul>"
        "<p>Machine-readable A5 artifacts: "
        "<code>candidate_evidence.csv</code>, "
        "<code>candidate_constraints.json</code>, "
        "<code>literature_whitespace.json</code>, "
        "<code>ranking_sensitivity.json</code>.</p>"
    )
    marker = "</body>"
    if marker in document:
        document = document.replace(marker, section + marker, 1)
    else:
        document += section
    report.write_text(document, encoding="utf-8")
    return True
