"""Transparent, missingness-aware candidate evidence and constraint filtering."""
from __future__ import annotations

import math

EVIDENCE_FIELDS = (
    "biological_evidence",
    "statistical_strength",
    "detectability",
    "blood_background_safety",
    "early_stage_score",
    "specificity_score",
    "literature_novelty",
    "literature_validation_gap",
    "literature_diagnostic_utility",
)
_UNAVAILABLE = "Data unavailable"


def _score(value):
    """Normalize a measured score to [0, 1]; never coerce invalid values to evidence."""
    if value is None or value == _UNAVAILABLE or isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(value):
        return None
    return max(0.0, min(1.0, value))


def _weight(value, key):
    """Weights must be explicit finite non-negative numbers."""
    if isinstance(value, bool):
        raise ValueError(f"Weight for {key!r} must be a finite non-negative number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"Weight for {key!r} must be a finite non-negative number") from exc
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"Weight for {key!r} must be a finite non-negative number")
    return result


def _constraint_bool(value, default=True):
    """Parse bool-like configuration values without bool('false') becoming True."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    return default


def _bounded_constraint(value, name, default):
    if value is None:
        value = default
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number between 0 and 1") from exc
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise ValueError(f"{name} must be a finite number between 0 and 1")
    return number


def normalize_evidence(candidate):
    row = dict(candidate or {})
    literature = row.get("literature") or {}
    aliases = {
        "literature_novelty": literature.get("novelty", row.get("literature_novelty")),
        "literature_validation_gap": literature.get("validation_gap", row.get("literature_validation_gap")),
        "literature_diagnostic_utility": literature.get("diagnostic_utility", row.get("literature_diagnostic_utility")),
    }
    for key in EVIDENCE_FIELDS:
        value = aliases.get(key, row.get(key))
        # Normalize invalid/non-finite measurements to the explicit unavailable
        # sentinel. Never leave None/NaN as if it were an observed value.
        normalized = _score(value)
        row[key] = normalized if normalized is not None else _UNAVAILABLE
    return row


def apply_constraints(
    candidate,
    min_detectability=0.0,
    max_background=1.0,
    require_assay=True,
    require_fpr=True,
):
    row = normalize_evidence(candidate)
    constraints = dict(row.get("constraints") or {})
    min_detectability = _bounded_constraint(min_detectability, "min_detectability", 0.0)
    max_background = _bounded_constraint(max_background, "max_background", 1.0)
    detectability = _score(row.get("detectability"))
    background = _score(row.get("blood_background_safety"))

    # Unknown detectability is not negative evidence. A positive minimum threshold,
    # however, cannot be satisfied without an observed detectability value.
    detectable = (
        min_detectability <= 0.0
        if detectability is None
        else detectability >= min_detectability
    )

    # This field is a safety score (higher is safer), not raw background burden.
    # Missing background safety does not become positive evidence or a measured
    # failure; it remains unobserved and is handled separately by the score layer.
    # When an explicit background ceiling is restrictive (< 1.0), an
    # unobserved background measurement cannot satisfy that safety constraint.
    # The default ceiling of 1.0 imposes no restriction, so missing background
    # remains unobserved rather than being treated as a positive measurement.
    background_safe = (
        max_background >= 1.0
        if background is None
        else background >= max(0.0, 1.0 - max_background)
    )

    assay_ok = _constraint_bool(constraints.get("assay_ok"), True) if require_assay else True
    fpr_ok = _constraint_bool(constraints.get("fpr_ok"), True) if require_fpr else True
    row["constraints"] = {
        **constraints,
        "detectable": bool(detectable),
        "background_safe": bool(background_safe),
        "assay_ok": bool(assay_ok),
        "fpr_ok": bool(fpr_ok),
        "eligible": bool(detectable and background_safe and assay_ok and fpr_ok),
    }
    return row


def evidence_vector(candidate):
    row = normalize_evidence(candidate)
    return {key: row[key] for key in EVIDENCE_FIELDS}


def transparent_weighted_score(candidate, weights):
    row = normalize_evidence(candidate)
    weights = dict(weights or {})
    normalized_weights = {
        key: _weight(weights.get(key, 0.0), key)
        for key in EVIDENCE_FIELDS
    }
    usable = {
        key: _score(row.get(key))
        for key in EVIDENCE_FIELDS
        if _score(row.get(key)) is not None and normalized_weights[key] > 0
    }
    total_weight = sum(normalized_weights[key] for key in usable)
    if total_weight <= 0:
        return {
            "score": None,
            "status": _UNAVAILABLE,
            "used_fields": [],
            "available_field_count": 0,
            "available_weight": 0.0,
        }
    score = sum(usable[key] * normalized_weights[key] for key in usable) / total_weight
    return {
        "score": score,
        "status": "Available",
        "used_fields": sorted(usable),
        "available_field_count": len(usable),
        "available_weight": total_weight,
    }


def rank_candidates(candidates, weights, constraints=None):
    """Rank eligible candidates only; return mutually exclusive result buckets."""
    constraints = dict(constraints or {})
    evaluated = []
    seen_ids = {}
    duplicate_ids = set()
    for candidate in candidates:
        row = apply_constraints(candidate, **constraints)
        scoring = transparent_weighted_score(row, weights)
        row["research_score"] = scoring["score"]
        row["score_status"] = scoring["status"]
        row["score_fields"] = scoring["used_fields"]
        row["score_available_field_count"] = scoring["available_field_count"]
        candidate_id = str(row.get("candidate_id") or row.get("feature") or row.get("candidate") or "")
        if candidate_id:
            if candidate_id in seen_ids:
                duplicate_ids.add(candidate_id)
            seen_ids[candidate_id] = seen_ids.get(candidate_id, 0) + 1
        evaluated.append(row)

    eligible = [row for row in evaluated if row["constraints"]["eligible"]]
    scored = [row for row in eligible if row["research_score"] is not None]
    unscored = [row for row in eligible if row["research_score"] is None]
    ineligible = [row for row in evaluated if not row["constraints"]["eligible"]]
    scored.sort(
        key=lambda row: (
            -row["research_score"],
            str(row.get("candidate_id") or row.get("feature") or row.get("candidate") or ""),
        )
    )
    return {
        "ranked": scored,
        "ineligible": ineligible,
        "unscored": unscored,
        "audit": {
            "candidate_count": len(evaluated),
            "ranked_count": len(scored),
            "ineligible_count": len(ineligible),
            "unscored_count": len(unscored),
            "duplicate_candidate_ids": sorted(duplicate_ids),
            "duplicate_candidate_id_count": len(duplicate_ids),
            "buckets_disjoint": len(scored) + len(ineligible) + len(unscored) == len(evaluated),
        },
    }
