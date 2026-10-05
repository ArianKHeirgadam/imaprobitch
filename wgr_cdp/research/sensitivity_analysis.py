"""Sensitivity analysis for transparent candidate-weight configurations."""
from __future__ import annotations

import math

from .evidence import rank_candidates

UNAVAILABLE = "Data unavailable"


def normalize_weights(weights):
    """Validate and normalize finite, explicit, non-negative weights."""
    raw = dict(weights or {})
    normalized = {}
    for key, value in raw.items():
        if isinstance(value, bool):
            raise ValueError(f"Weight for {key!r} must be a finite non-negative number")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"Weight for {key!r} must be a finite non-negative number") from exc
        if not math.isfinite(number) or number < 0:
            raise ValueError(f"Weight for {key!r} must be a finite non-negative number")
        normalized_key = str(key)
        if normalized_key not in {
            "biological_evidence", "statistical_strength", "detectability",
            "blood_background_safety", "early_stage_score", "specificity_score",
            "literature_novelty", "literature_validation_gap",
            "literature_diagnostic_utility", "recurrence_prevalence",
            "cfdna_suitability", "patient_coverage",
            "external_cancer_evidence",
        }:
            raise ValueError(f"Unknown evidence weight field: {normalized_key!r}")
        normalized[normalized_key] = number
    total = sum(normalized.values())
    if not math.isfinite(total) or total <= 0:
        raise ValueError("at least one weight must be positive")
    return {key: value / total for key, value in normalized.items()}


def weight_sensitivity(candidates, base_weights, scenarios, constraints=None):
    """Re-rank the same candidate universe across explicit weight scenarios."""
    base = normalize_weights(base_weights)
    results = []
    for scenario in scenarios:
        try:
            name, overrides = scenario
        except (TypeError, ValueError) as exc:
            raise ValueError("Each sensitivity scenario must be a (name, overrides) pair") from exc
        weights = dict(base)
        weights.update(dict(overrides or {}))
        weights = normalize_weights(weights)
        ranking = rank_candidates(candidates, weights, constraints or {})
        ranked_candidates = [
            str(row.get("candidate_id") or row.get("feature") or row.get("candidate") or "")
            for row in ranking["ranked"]
        ]
        results.append({
            "scenario": str(name),
            "weights": weights,
            "ranked_candidates": ranked_candidates,
            "top_candidate": ranked_candidates[0] if ranked_candidates else None,
            "ranked_count": len(ranking["ranked"]),
            "ineligible_count": len(ranking["ineligible"]),
            "unscored_count": len(ranking["unscored"]),
        })
    return results


def selection_stability(results, k=15):
    """Summarize top-candidate and top-K selection stability."""
    k = min(15, max(0, int(k)))
    valid = [r for r in results if r.get("ranked_candidates")]
    counts = {}
    for row in valid:
        top = row["ranked_candidates"][0]
        counts[top] = counts.get(top, 0) + 1
    top_total = len(valid)

    top_sets = [set(row.get("ranked_candidates", [])[:k]) for row in valid]
    pairwise = []
    for index in range(len(top_sets)):
        for other in range(index + 1, len(top_sets)):
            union = top_sets[index] | top_sets[other]
            pairwise.append(
                len(top_sets[index] & top_sets[other]) / len(union)
                if union else 1.0
            )

    return {
        "n_scenarios": len(results),
        "n_valid_scenarios": top_total,
        "top_candidate_frequency": {
            key: value / top_total for key, value in sorted(counts.items())
        } if top_total else {},
        "top_candidate": max(counts, key=counts.get) if counts else None,
        "unique_top_candidates": len(counts),
        "top_k_pairwise_jaccard_mean": (
            sum(pairwise) / len(pairwise) if pairwise else (1.0 if len(top_sets) == 1 else UNAVAILABLE)
        ),
        "pairwise_comparisons": len(pairwise),
        "status": "Available" if top_total else UNAVAILABLE,
    }
