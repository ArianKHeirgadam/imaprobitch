"""Phase A7: final multimodal candidate integration and panel design.

This module is the terminal research-design layer. It consumes the complete
auditable candidate evidence table, preserves unavailable measurements, applies
hard constraints before ranking, and then optimizes patient coverage over the
full eligible candidate universe when a patient-by-candidate detectability
matrix is available.

It does not manufacture biological, clinical, or validation evidence.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .evidence import rank_candidates
from .panel_optimizer import (
    alpha_budget,
    greedy_panel,
    ilp_panel,
    panel_coverage,
    coverage_curve,
    greedy_vs_ilp,
    panel_bootstrap_stability,
    layer_contribution,
)
from .a5_integration import DEFAULT_WEIGHTS
from .patient_coverage import panel_presence_coverage, greedy_presence_panel, exact_presence_panel


def load_multimodal_evidence(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _f(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _available(row, *names):
    for name in names:
        value = _f(row.get(name))
        if value is not None:
            return value
    return None


def multimodal_to_candidates(rows):
    """Map the real multimodal comparison schema into A5/A7 evidence fields."""
    out = []
    for row in rows:
        feature = row.get("feature")
        if not feature:
            continue
        diff = _available(row, "frequency_difference", "case_frequency_difference")
        detect = _available(row, "detectability", "detectability_score", "power")
        bg = _available(row, "blood_background", "blood_background_max")
        early = _available(row, "early_stage_fraction", "early_stage_score")
        specificity = _available(row, "specificity", "specificity_score")
        q_value = _available(row, "q_value", "fdr", "adjusted_p_value")
        p_value = _available(row, "p_value")
        statistical = None if q_value is None else max(0.0, min(1.0, 1.0 - q_value))
        out.append({
            "candidate_id": str(feature),
            "feature": str(feature),
            "gene": row.get("gene") or "",
            "candidate_type": row.get("feature_type") or "",
            "biological_evidence": _available(row, "biological_evidence"),
            "statistical_strength": statistical if statistical is not None else "Data unavailable",
            "detectability": detect if detect is not None else "Data unavailable",
            "blood_background_safety": (
                max(0.0, min(1.0, 1.0 - bg)) if bg is not None else "Data unavailable"
            ),
            "early_stage_score": early if early is not None else "Data unavailable",
            "specificity_score": specificity if specificity is not None else "Data unavailable",
            "literature_novelty": _available(row, "literature_novelty"),
            "literature_validation_gap": _available(row, "literature_validation_gap"),
            "literature_diagnostic_utility": _available(row, "literature_diagnostic_utility"),
            "frequency_difference": diff,
            "p_value": p_value,
            "q_value": q_value,
            "validation_status": row.get("validation_status") or "Data unavailable",
            "constraints": {
                "assay_ok": str(row.get("assay_ok", "true")).lower() not in {"false", "0", "no"},
                "fpr_ok": str(row.get("fpr_ok", "true")).lower() not in {"false", "0", "no"},
            },
        })
    return out


def _matrix_for_candidates(matrix, candidate_ids):
    if not matrix:
        return None
    ids = set(candidate_ids)
    restricted = {}
    for patient, row in matrix.items():
        restricted[patient] = {
            candidate: float(row.get(candidate, 0.0) or 0.0)
            for candidate in ids
            if candidate in row
        }
    return restricted if any(restricted.values()) else None


def _presence_for_candidates(matrix, candidate_ids):
    if not matrix:
        return None
    ids = set(candidate_ids)
    restricted = {}
    for patient, row in matrix.items():
        restricted[patient] = {
            candidate: int(row[candidate])
            for candidate in ids
            if candidate in row and row[candidate] in (0, 1)
        }
    return restricted if any(restricted.values()) else None


def _panel_optimize_presence(matrix, max_k, min_gain=0.02):
    if not matrix:
        return {"status": "Data unavailable", "method": "not_run", "selected": [], "coverage": "Data unavailable", "k": 0}
    candidate_count = len({candidate for row in matrix.values() for candidate in row})
    if candidate_count <= 22:
        exact = exact_presence_panel(matrix, max_k=min(15, int(max_k)), min_gain=float(min_gain))
        if exact.get("status") == "Available":
            return exact
    return greedy_presence_panel(matrix, max_k=min(15, int(max_k)), min_gain=float(min_gain))


def _panel_optimize(matrix, max_k, fpr_target, min_gain=0.02):
    if not matrix:
        return {
            "status": "Data unavailable",
            "method": "not_run",
            "selected": [],
            "coverage": "Data unavailable",
            "k": 0,
            "alpha_per_feature": None,
        }

    candidate_count = len({candidate for row in matrix.values() for candidate in row})
    if candidate_count <= 22:
        panel = ilp_panel(matrix, max_k=min(15, int(max_k)), min_gain=float(min_gain))
        method = panel.get("method", "exact_0_1")
        if panel.get("status") == "optimal":
            selected = panel["selected"]
            coverage = panel["coverage"]
        else:
            fallback = greedy_panel(matrix, max_k=min(15, int(max_k)), min_gain=float(min_gain))
            selected, coverage = fallback["selected"], fallback["coverage"]
            method = "greedy_fallback"
    else:
        fallback = greedy_panel(matrix, max_k=min(15, int(max_k)), min_gain=float(min_gain))
        selected, coverage = fallback["selected"], fallback["coverage"]
        method = "greedy"

    k = len(selected)
    return {
        "status": "Available",
        "method": method,
        "selected": selected,
        "coverage": coverage,
        "k": k,
        "alpha_per_feature": alpha_budget(fpr_target, max(1, k)),
        "candidate_universe_n": candidate_count,
    }


def build_final_panel(
    candidates,
    matrix=None,
    presence_matrix=None,
    max_k=15,
    fpr_target=0.05,
    weights=None,
    constraints=None,
    min_gain=0.02,
    bootstrap=200,
    candidate_layers=None,
    presence_matrix=None,
):
    """Produce the final ranked candidate set and complementary coverage panel."""
    weights = dict(weights or DEFAULT_WEIGHTS)
    constraints = dict(constraints or {"min_detectability": 0.0, "max_background": 1.0})

    ranking = rank_candidates(candidates, weights, constraints)
    eligible = ranking["ranked"]
    eligible_ids = [
        str(row.get("candidate_id") or row.get("feature") or row.get("candidate"))
        for row in eligible
    ]

    # Optimize across the entire eligible universe, not merely the first K ranks.
    restricted = _matrix_for_candidates(matrix, eligible_ids)
    restricted_presence = _presence_for_candidates(presence_matrix, eligible_ids)
    effective_k = min(15, max(0, int(max_k)))
    probability_optimization = _panel_optimize(
        restricted, effective_k, fpr_target, min_gain=min_gain
    )
    presence_optimization = _panel_optimize_presence(
        restricted_presence, effective_k, min_gain=min_gain
    )
    optimization = presence_optimization if presence_optimization.get("status") == "Available" else probability_optimization

    diagnostics = {
        "coverage_curve": coverage_curve(restricted, effective_k, min_gain=min_gain) if restricted else "Data unavailable",
        "greedy_vs_ilp": greedy_vs_ilp(restricted, effective_k, min_gain=min_gain) if restricted else "Data unavailable",
        "panel_bootstrap_stability": panel_bootstrap_stability(restricted, effective_k, bootstrap, 42) if restricted else "Data unavailable",
        "layer_contribution": layer_contribution(
            restricted,
            optimization.get("selected", []),
            candidate_layers or {},
        ) if restricted and candidate_layers else "Data unavailable",
        "selection_objective": "patient_presence" if presence_optimization.get("status") == "Available" else "probabilistic_detectability",
        "probability_optimization": probability_optimization,
        "presence_optimization": presence_optimization,
    }

    if optimization["status"] == "Available":
        selected_ids = optimization["selected"]
    else:
        selected_ids = eligible_ids[: int(max_k)]

    ranked_top_k = eligible_ids[: int(max_k)]
    selected_coverage = (
        panel_presence_coverage(restricted_presence, selected_ids)["coverage"]
        if restricted_presence is not None
        else panel_coverage(restricted, selected_ids)
        if restricted is not None
        else "Data unavailable"
    )
    probability_coverage = (
        panel_coverage(restricted, selected_ids)
        if restricted is not None else "Data unavailable"
    )
    presence_coverage = (
        panel_presence_coverage(restricted_presence, selected_ids)
        if restricted_presence is not None else "Data unavailable"
    )

    return {
        "status": "Available" if candidates else "Data unavailable",
        "constraints": constraints,
        "weights": weights,
        "candidate_count": len(candidates),
        "eligible_count": len(eligible),
        "ineligible_count": len(ranking["ineligible"]),
        "unscored_count": len(ranking["unscored"]),
        "ranked_candidates": ranked_top_k,
        "eligible_candidate_ids": eligible_ids,
        "panel": {
            **optimization,
            "selected": selected_ids,
            "coverage": selected_coverage,
            "probability_coverage": probability_coverage,
            "presence_coverage": presence_coverage,
            "max_k": effective_k,
            "min_marginal_gain": float(min_gain),
        },
        "diagnostics": diagnostics,
        "fpr_target": float(fpr_target),
    }


def write_final_panel(
    output_dir,
    candidates,
    matrix=None,
    max_k=15,
    fpr_target=0.05,
    weights=None,
    constraints=None,
    min_gain=0.02,
    bootstrap=200,
    candidate_layers=None,
):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    weights = dict(weights or DEFAULT_WEIGHTS)
    constraints = dict(constraints or {"min_detectability": 0.0, "max_background": 1.0})

    result = build_final_panel(
        candidates,
        matrix=matrix,
        presence_matrix=presence_matrix,
        max_k=max_k,
        fpr_target=fpr_target,
        weights=weights,
        constraints=constraints,
        min_gain=min_gain,
        bootstrap=bootstrap,
        candidate_layers=candidate_layers,
    )

    (output / "final_panel.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8"
    )

    ranking = rank_candidates(candidates, weights, constraints)
    selected = set(result["panel"]["selected"])
    fields = [
        "rank", "selected", "candidate_id", "feature", "gene", "candidate_type",
        "p_value", "q_value", "detectability", "blood_background_safety",
        "early_stage_score", "specificity_score", "research_score", "score_status",
    ]
    with (output / "final_panel_candidates.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for index, row in enumerate(ranking["ranked"], 1):
            item = dict(row)
            item["rank"] = index
            item["selected"] = str(item.get("candidate_id") or item.get("feature")) in selected
            writer.writerow(item)

    (output / "final_panel_diagnostics.json").write_text(
        json.dumps(result.get("diagnostics", {}), indent=2, default=str),
        encoding="utf-8",
    )

    (output / "final_panel_constraints.json").write_text(
        json.dumps({
            "constraints": constraints,
            "fpr_target": float(fpr_target),
            "max_k": min(15, int(max_k)),
            "min_marginal_gain": float(min_gain),
            "bootstrap": int(bootstrap),
            "weights": weights,
            "candidate_count": len(candidates),
            "eligible_count": len(ranking["ranked"]),
            "ineligible_count": len(ranking["ineligible"]),
            "unscored_count": len(ranking["unscored"]),
        }, indent=2, default=str),
        encoding="utf-8",
    )
    return result


def append_a7_to_report(output_dir, result):
    """Append the final-panel audit summary without changing prior report sections."""
    report = Path(output_dir) / "report.html"
    if not report.exists():
        return False
    import html
    panel = result.get("panel", {})
    selected = panel.get("selected", [])
    coverage = panel.get("coverage", "Data unavailable")
    section = (
        "<hr><h2>Phase A7 Final Panel</h2>"
        "<p>Final panel construction is a research-design result, not a clinical diagnostic claim.</p>"
        f"<ul><li>Eligible candidates: {int(result.get('eligible_count', 0))}</li>"
        f"<li>Panel size: {int(panel.get('k', 0))}</li>"
        f"<li>Panel method: {html.escape(str(panel.get('method', 'not_run')))}</li>"
        f"<li>Patient coverage: {html.escape(str(coverage))}</li>"
        f"<li>Per-feature FPR budget: {html.escape(str(panel.get('alpha_per_feature', 'Data unavailable')))}</li></ul>"
        "<p>Machine-readable A7 artifacts: "
        "<code>final_panel.json</code>, <code>final_panel_candidates.csv</code>, "
        "<code>final_panel_constraints.json</code>.</p>"
    )
    marker = "</body>"
    report = report.read_text(encoding="utf-8")
    report = report.replace(marker, section + marker, 1) if marker in report else report + section
    Path(output_dir, "report.html").write_text(report, encoding="utf-8")
    return True
