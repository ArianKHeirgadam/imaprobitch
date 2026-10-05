"""C-12.6: evidence-strength confidence for candidate prioritization."""
from __future__ import annotations

import math

UNAVAILABLE = "Data unavailable"

DEFAULT_CONFIDENCE = {
    "high_min_score": 0.75,
    "moderate_min_score": 0.50,
    "high_min_components": 5,
    "moderate_min_components": 3,
    "high_min_stability": 0.80,
}


def _finite(value):
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return value if math.isfinite(value) else None


def evidence_strength_confidence(
    row,
    *,
    stability=None,
    validation_status=None,
    thresholds=None,
):
    thresholds = dict(DEFAULT_CONFIDENCE if thresholds is None else thresholds)
    score = _finite(row.get("research_score"))
    fields = row.get("score_fields") or []
    component_count = len(fields)
    stability_value = _finite(stability)
    validation = validation_status or row.get("validation_status") or UNAVAILABLE

    if score is None or component_count == 0:
        level = UNAVAILABLE
        rationale = "No numeric composite score with observed evidence components."
    elif score >= thresholds["high_min_score"] and component_count >= int(thresholds["high_min_components"]):
        if stability_value is None or stability_value >= thresholds["high_min_stability"]:
            level = "HIGH"
            rationale = "Strong computational evidence across multiple observed components."
        else:
            level = "MODERATE"
            rationale = "Strong score but ranking/selection stability is below the high-confidence threshold."
    elif score >= thresholds["moderate_min_score"] and component_count >= int(thresholds["moderate_min_components"]):
        level = "MODERATE"
        rationale = "Moderate computational evidence across multiple observed components."
    else:
        level = "LOW"
        rationale = "Evidence is limited or composite support is weak."

    return {
        "level": level,
        "score": score if score is not None else UNAVAILABLE,
        "observed_component_count": component_count,
        "observed_components": list(fields),
        "stability": stability_value if stability_value is not None else UNAVAILABLE,
        "validation_status": validation,
        "meaning": (
            "Confidence denotes strength of computational evidence for candidate "
            "prioritization, not probability of cancer or clinical diagnosis."
        ),
        "rationale": rationale,
        "thresholds": thresholds,
    }
