"""Phase C-09: robustness and sensitivity analysis.

The functions in this module stress-test research ranking and panel selection
under transparent computational perturbations. They do not create biological
evidence and do not replace external validation.

All perturbations are explicitly labelled. Missing evidence remains
"Data unavailable"; missing patient-by-candidate observations are handled by
the existing observation-aware panel coverage implementation.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from random import Random

from .evidence import EVIDENCE_FIELDS, normalize_evidence, rank_candidates
from .panel_optimizer import greedy_panel, panel_coverage
from .sensitivity_analysis import normalize_weights, selection_stability, weight_sensitivity

UNAVAILABLE = "Data unavailable"

_LITERATURE_ALIASES = {
    "literature_novelty": "novelty",
    "literature_validation_gap": "validation_gap",
    "literature_diagnostic_utility": "diagnostic_utility",
}


def _candidate_id(row):
    return str(row.get("candidate_id") or row.get("feature") or row.get("candidate") or "")


def _finite_01(value, name):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number between 0 and 1") from exc
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be a finite number between 0 and 1")
    return number


def _normalize_k_values(values, max_k=15):
    try:
        cap = min(15, max(0, int(max_k)))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("max_k must be an integer") from exc
    if cap == 0:
        return [0]
    normalized = set()
    for value in values:
        try:
            item = int(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("K values must be integers") from exc
        if item < 0:
            raise ValueError("K values must be non-negative")
        normalized.add(min(15, item))
    return sorted(item for item in normalized if item <= cap)


def _jaccard(left, right):
    a, b = set(left), set(right)
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def ranking_robustness(results, k=15):
    """Summarize agreement among ranked candidate lists."""
    valid = [row for row in results if row.get("ranked_candidates")]
    top_frequency = selection_stability(results, k=k)
    top_sets = [set(row.get("ranked_candidates", [])[:max(0, min(15, int(k)))]) for row in valid]
    pairwise = []
    for index in range(len(top_sets)):
        for other in range(index + 1, len(top_sets)):
            pairwise.append(_jaccard(top_sets[index], top_sets[other]))
    return {
        "status": "Available" if valid else UNAVAILABLE,
        "n_scenarios": len(results),
        "n_valid_scenarios": len(valid),
        "k": min(15, max(0, int(k))),
        "pairwise_jaccard_mean": (
            sum(pairwise) / len(pairwise) if pairwise else (1.0 if len(top_sets) == 1 else UNAVAILABLE)
        ),
        "pairwise_comparisons": len(pairwise),
        **top_frequency,
    }


def threshold_sensitivity(candidates, base_weights, detectability_thresholds,
                          background_thresholds, base_constraints=None, k=15):
    """Evaluate deterministic ranking across hard-constraint threshold grids."""
    constraints = dict(base_constraints or {})
    detectability = sorted({_finite_01(value, "detectability threshold") for value in detectability_thresholds})
    background = sorted({_finite_01(value, "background threshold") for value in background_thresholds}, reverse=True)
    baseline_ranking = rank_candidates(candidates, base_weights, constraints)
    baseline_ids = [
        _candidate_id(row) for row in baseline_ranking["ranked"]
    ]
    scenarios = []
    for d in detectability:
        for b in background:
            scenario_constraints = dict(constraints)
            scenario_constraints["min_detectability"] = d
            scenario_constraints["max_background"] = b
            ranking = rank_candidates(candidates, base_weights, scenario_constraints)
            ranked_ids = [_candidate_id(row) for row in ranking["ranked"]]
            scenarios.append({
                "scenario": f"detectability>={d:.6g};max_background<={b:.6g}",
                "min_detectability": d,
                "max_background": b,
                "ranked_candidates": ranked_ids,
                "top_candidate": ranked_ids[0] if ranked_ids else None,
                "ranked_count": len(ranking["ranked"]),
                "ineligible_count": len(ranking["ineligible"]),
                "unscored_count": len(ranking["unscored"]),
                "k_overlap_reference": len(set(ranked_ids[:k]) & set(baseline_ids[:k])),
                "k_jaccard_reference": _jaccard(ranked_ids[:k], baseline_ids[:k]),
            })
    return scenarios


def k_sensitivity(matrix, k_values=tuple(range(1, 16)), min_gain=0.02):
    """Evaluate deterministic greedy panel selection across K values.

    Panel coverage uses the existing observation-aware denominator. Missing
    patient-by-candidate cells are not converted to explicit zero observations.
    """
    if not matrix:
        return {"status": UNAVAILABLE, "results": []}
    try:
        gain = float(min_gain)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("min_gain must be a finite non-negative number") from exc
    if not math.isfinite(gain) or gain < 0:
        raise ValueError("min_gain must be a finite non-negative number")
    ks = _normalize_k_values(k_values, max_k=15)
    results = []
    previous = []
    for k in ks:
        if k == 0:
            selected = []
            coverage = 0.0
            method = "empty_panel"
        else:
            panel = greedy_panel(matrix, max_k=k, min_gain=gain)
            selected = list(panel["selected"])
            coverage = panel["coverage"]
            method = panel["method"]
        row = {
            "k": k,
            "selected": selected,
            "selected_count": len(selected),
            "coverage": coverage,
            "method": method,
            "jaccard_vs_previous": _jaccard(selected, previous) if previous else UNAVAILABLE,
        }
        results.append(row)
        previous = selected
    return {
        "status": "Available",
        "min_gain": gain,
        "max_k": max(ks) if ks else 0,
        "results": results,
    }


def missingness_stress(candidates, base_weights, missingness_rates,
                       constraints=None, repeats=10, k=15, seed=42):
    """Stress-test ranking by synthetically masking observed evidence fields.

    This is an engineering perturbation, not a biological result. It is based
    only on the supplied candidates and is never written back to source data.
    """
    try:
        n_repeats = int(repeats)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("repeats must be an integer") from exc
    if n_repeats <= 0:
        return {
            "status": UNAVAILABLE,
            "perturbation_model": "synthetic_missingness_masking",
            "n_repeats": 0,
            "results": [],
        }

    rates = sorted({_finite_01(value, "missingness rate") for value in missingness_rates})
    rng = Random(int(seed))
    baseline_ranking = rank_candidates(candidates, base_weights, constraints or {})
    baseline_ids = [_candidate_id(row) for row in baseline_ranking["ranked"]]
    results = []

    for rate in rates:
        top_counts = {}
        selected_counts = {}
        valid_repeats = 0
        for _ in range(n_repeats):
            perturbed = []
            for original in candidates:
                row = normalize_evidence(original)
                row["literature"] = dict(row.get("literature") or {})
                for field in EVIDENCE_FIELDS:
                    if row.get(field) == UNAVAILABLE:
                        continue
                    if rng.random() < rate:
                        row[field] = UNAVAILABLE
                        alias = _LITERATURE_ALIASES.get(field)
                        if alias:
                            row["literature"].pop(alias, None)
                perturbed.append(row)

            ranking = rank_candidates(perturbed, base_weights, constraints or {})
            ranked_ids = [_candidate_id(item) for item in ranking["ranked"]]
            if ranked_ids:
                valid_repeats += 1
                top_counts[ranked_ids[0]] = top_counts.get(ranked_ids[0], 0) + 1
            for candidate in ranked_ids[:max(0, min(15, int(k)))]:
                selected_counts[candidate] = selected_counts.get(candidate, 0) + 1

        results.append({
            "missingness_rate": rate,
            "n_repeats": n_repeats,
            "n_valid_repeats": valid_repeats,
            "top_candidate_frequency": {
                candidate: count / valid_repeats for candidate, count in sorted(top_counts.items())
            } if valid_repeats else {},
            "top_candidate_retention": (
                top_counts.get(baseline_ids[0], 0) / valid_repeats
                if baseline_ids and valid_repeats else UNAVAILABLE
            ),
            "selection_frequency_at_k": {
                candidate: count / n_repeats
                for candidate, count in sorted(selected_counts.items())
            },
        })

    return {
        "status": "Available",
        "perturbation_model": "synthetic_missingness_masking",
        "seed": int(seed),
        "n_repeats": n_repeats,
        "k": min(15, max(0, int(k))),
        "baseline_top_candidate": baseline_ids[0] if baseline_ids else None,
        "baseline_ranked_count": len(baseline_ids),
        "results": results,
    }


def run_c09_robustness(
    candidates,
    base_weights=None,
    constraints=None,
    matrix=None,
    weight_scenarios=None,
    detectability_thresholds=(0.0, 0.25, 0.5, 0.75),
    background_thresholds=(1.0, 0.75, 0.5, 0.25),
    k_values=tuple(range(1, 16)),
    missingness_rates=(0.0, 0.10, 0.25, 0.50),
    missingness_repeats=10,
    min_gain=0.02,
    seed=42,
    k=15,
):
    """Run the complete C-09 robustness suite without modifying source inputs."""
    if not candidates:
        return {
            "status": UNAVAILABLE,
            "schema_version": "c09.robustness.v1",
            "weight_sensitivity": [],
            "weight_robustness": {"status": UNAVAILABLE},
            "threshold_sensitivity": [],
            "k_sensitivity": {"status": UNAVAILABLE, "results": []},
            "missingness_stress": {"status": UNAVAILABLE, "results": []},
        }

    base_weights = dict(base_weights or {field: 1.0 for field in EVIDENCE_FIELDS})
    constraints = dict(constraints or {})
    if weight_scenarios is None:
        weight_scenarios = [
            ("baseline", {}),
            ("detectability_2x", {"detectability": 2.0}),
            ("statistical_strength_2x", {"statistical_strength": 2.0}),
            ("blood_background_safety_2x", {"blood_background_safety": 2.0}),
            ("early_stage_2x", {"early_stage_score": 2.0}),
            ("specificity_2x", {"specificity_score": 2.0}),
        ]

    weights = normalize_weights(base_weights)
    weight_results = weight_sensitivity(candidates, weights, weight_scenarios, constraints)
    threshold_results = threshold_sensitivity(
        candidates,
        weights,
        detectability_thresholds,
        background_thresholds,
        constraints,
        k=k,
    )
    k_results = k_sensitivity(matrix, k_values=k_values, min_gain=min_gain)
    missing_results = missingness_stress(
        candidates,
        weights,
        missingness_rates,
        constraints=constraints,
        repeats=missingness_repeats,
        k=k,
        seed=seed,
    )

    return {
        "status": "Available",
        "schema_version": "c09.robustness.v1",
        "seed": int(seed),
        "k": min(15, max(0, int(k))),
        "weights": weights,
        "constraints": constraints,
        "weight_sensitivity": weight_results,
        "weight_robustness": ranking_robustness(weight_results, k=k),
        "threshold_sensitivity": threshold_results,
        "threshold_robustness": ranking_robustness(threshold_results, k=k),
        "k_sensitivity": k_results,
        "missingness_stress": missing_results,
        "scientific_boundary": (
            "Robustness outputs are deterministic computational stress tests. "
            "They do not establish clinical validity, biological causality, "
            "assay-validated LoD, or independent validation performance."
        ),
    }


def write_c09_artifacts(output_dir, candidates, **kwargs):
    """Persist the complete C-09 JSON/CSV audit bundle."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result = run_c09_robustness(candidates, **kwargs)

    json_path = output / "c09_robustness.json"
    json_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    weight_rows = [
        {
            "scenario": row.get("scenario"),
            "top_candidate": row.get("top_candidate"),
            "ranked_count": row.get("ranked_count", len(row.get("ranked_candidates", []))),
            "ineligible_count": row.get("ineligible_count", "Data unavailable"),
            "unscored_count": row.get("unscored_count", "Data unavailable"),
        }
        for row in result.get("weight_sensitivity", [])
    ]
    threshold_rows = [
        {
            "scenario": row.get("scenario"),
            "min_detectability": row.get("min_detectability"),
            "max_background": row.get("max_background"),
            "top_candidate": row.get("top_candidate"),
            "ranked_count": row.get("ranked_count"),
            "ineligible_count": row.get("ineligible_count"),
            "unscored_count": row.get("unscored_count"),
        }
        for row in result.get("threshold_sensitivity", [])
    ]
    k_rows = [
        {
            "k": row.get("k"),
            "selected_count": row.get("selected_count"),
            "coverage": row.get("coverage"),
            "method": row.get("method"),
            "jaccard_vs_previous": row.get("jaccard_vs_previous"),
            "selected": "|".join(row.get("selected", [])),
        }
        for row in result.get("k_sensitivity", {}).get("results", [])
    ]
    missing_rows = []
    for row in result.get("missingness_stress", {}).get("results", []):
        missing_rows.append({
            "missingness_rate": row.get("missingness_rate"),
            "n_repeats": row.get("n_repeats"),
            "n_valid_repeats": row.get("n_valid_repeats"),
            "baseline_top_candidate": result.get("missingness_stress", {}).get("baseline_top_candidate"),
            "top_candidate_retention": row.get("top_candidate_retention"),
            "top_candidate_frequency": json.dumps(row.get("top_candidate_frequency", {}), sort_keys=True),
        })

    artifacts = {
        "c09_robustness": str(json_path),
        "c09_weight_sensitivity": str(output / "c09_weight_sensitivity.csv"),
        "c09_threshold_sensitivity": str(output / "c09_threshold_sensitivity.csv"),
        "c09_k_sensitivity": str(output / "c09_k_sensitivity.csv"),
        "c09_missingness_stress": str(output / "c09_missingness_stress.csv"),
    }

    for path, rows in (
        (Path(artifacts["c09_weight_sensitivity"]), weight_rows),
        (Path(artifacts["c09_threshold_sensitivity"]), threshold_rows),
        (Path(artifacts["c09_k_sensitivity"]), k_rows),
        (Path(artifacts["c09_missingness_stress"]), missing_rows),
    ):
        fields = sorted({key for row in rows for key in row}) or ["status"]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    return {
        **result,
        "artifacts": artifacts,
    }


def append_c09_to_report(output_dir, result):
    """Append a concise C-09 audit summary to the existing HTML report."""
    report_path = Path(output_dir) / "report.html"
    if not report_path.exists():
        return False
    report = report_path.read_text(encoding="utf-8")
    weight_n = len(result.get("weight_sensitivity", []))
    threshold_n = len(result.get("threshold_sensitivity", []))
    k_n = len(result.get("k_sensitivity", {}).get("results", []))
    missing_n = len(result.get("missingness_stress", {}).get("results", []))
    weight_status = result.get("weight_robustness", {}).get("status", UNAVAILABLE)
    threshold_status = result.get("threshold_robustness", {}).get("status", UNAVAILABLE)
    section = (
        "<hr><h2>Phase C-09 Robustness &amp; Sensitivity</h2>"
        "<p>C-09 reports deterministic computational stress tests only; it does not "
        "establish clinical validity or assay performance.</p>"
        f"<ul><li>Weight scenarios: {weight_n}</li>"
        f"<li>Weight robustness status: {weight_status}</li>"
        f"<li>Threshold scenarios: {threshold_n}</li>"
        f"<li>Threshold robustness status: {threshold_status}</li>"
        f"<li>K-sensitivity points: {k_n}</li>"
        f"<li>Missingness stress rates: {missing_n}</li></ul>"
        "<p>Machine-readable C-09 artifacts: "
        "<code>c09_robustness.json</code>, "
        "<code>c09_weight_sensitivity.csv</code>, "
        "<code>c09_threshold_sensitivity.csv</code>, "
        "<code>c09_k_sensitivity.csv</code>, "
        "<code>c09_missingness_stress.csv</code>.</p>"
    )
    marker = "</body>"
    report = report.replace(marker, section + marker, 1) if marker in report else report + section
    report_path.write_text(report, encoding="utf-8")
    return True
