"""C-12.1: explicit cfDNA-oriented candidate suitability prioritization.

The layer distinguishes modeled assay detectability from broader liquid-biopsy
suitability. Every component is optional and only observed values contribute.
No component is inferred from a literature count or from missing data.
"""
from __future__ import annotations

import math

UNAVAILABLE = "Data unavailable"

DEFAULT_CFDNA_WEIGHTS = {
    "detectability": 0.25,
    "recurrence_prevalence": 0.20,
    "clonality": 0.15,
    "allele_fraction": 0.10,
    "mappability": 0.15,
    "prior_cfdna_evidence": 0.10,
    "alteration_type_support": 0.05,
}

_FIELD_ALIASES = {
    "clonality": ("clonality", "cancer_cell_fraction", "ccf"),
    "allele_fraction": ("allele_fraction", "vaf", "variant_allele_fraction"),
    "mappability": ("unique_mappability", "mappability", "unique_mapping"),
    "prior_cfdna_evidence": (
        "prior_cfdna_evidence",
        "cfDNA_evidence_score",
        "cfdna_evidence_score",
    ),
    "alteration_type_support": (
        "alteration_type_support",
        "cfDNA_type_support",
        "cfdna_type_support",
    ),
}


def _score(value):
    if value is None or value == UNAVAILABLE or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number):
        return None
    return max(0.0, min(1.0, number))


def _get_score(row, key):
    for alias in _FIELD_ALIASES.get(key, (key,)):
        score = _score(row.get(alias))
        if score is not None:
            return score
    return None


def _candidate_id(row):
    return str(row.get("candidate_id") or row.get("feature") or row.get("candidate") or "")


def recurrence_prevalence(row):
    value = _score(row.get("case_frequency"))
    if value is not None:
        return value
    try:
        n = float(row.get("case_n"))
        carriers = float(row.get("case_carriers"))
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(n) or not math.isfinite(carriers) or n <= 0 or carriers < 0:
        return None
    return max(0.0, min(1.0, carriers / n))


def patient_coverage(matrix, candidate_id):
    """Return observed patient-level coverage for an explicit binary/probability matrix."""
    if not matrix:
        return None
    covered = 0
    observed = 0
    for row in matrix.values():
        if candidate_id not in row:
            continue
        value = row.get(candidate_id)
        if value in (None, UNAVAILABLE):
            continue
        try:
            value = float(value)
        except (TypeError, ValueError, OverflowError):
            continue
        if not math.isfinite(value):
            continue
        observed += 1
        if value > 0:
            covered += 1
    return covered / observed if observed else None


def build_cfdna_suitability(row, matrix=None, weights=None):
    """Calculate a reproducible liquid-biopsy suitability priority."""
    row = dict(row or {})
    weights = dict(DEFAULT_CFDNA_WEIGHTS if weights is None else weights)
    components = {
        "detectability": _score(row.get("detectability")),
        "recurrence_prevalence": recurrence_prevalence(row),
        "clonality": _get_score(row, "clonality"),
        "allele_fraction": _get_score(row, "allele_fraction"),
        "mappability": _get_score(row, "mappability"),
        "prior_cfdna_evidence": _get_score(row, "prior_cfdna_evidence"),
        "alteration_type_support": _get_score(row, "alteration_type_support"),
    }
    usable = {}
    for key, value in components.items():
        weight = weights.get(key, 0.0)
        try:
            weight = float(weight)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"cfDNA weight for {key!r} must be finite and non-negative") from exc
        if not math.isfinite(weight) or weight < 0:
            raise ValueError(f"cfDNA weight for {key!r} must be finite and non-negative")
        if value is not None and weight > 0:
            usable[key] = (value, weight)

    coverage = patient_coverage(matrix, _candidate_id(row)) if matrix else None
    if coverage is not None:
        components["patient_coverage"] = coverage

    total_weight = sum(weight for _, weight in usable.values())
    score = (
        sum(value * weight for value, weight in usable.values()) / total_weight
        if total_weight > 0 else None
    )
    return {
        "candidate_id": _candidate_id(row),
        "score": score if score is not None else UNAVAILABLE,
        "status": "Available" if score is not None else UNAVAILABLE,
        "components": {
            key: (value if value is not None else UNAVAILABLE)
            for key, value in components.items()
        },
        "used_components": sorted(usable),
        "weight_sum_used": total_weight,
        "weights": weights,
        "interpretation": (
            "cfDNA suitability priority is a research prioritization signal; "
            "it is not proof of laboratory detectability."
        ),
    }


def augment_candidate(row, matrix=None, weights=None):
    """Add C-12 cfDNA and recurrence fields without mutating the input row."""
    output = dict(row or {})
    output["recurrence_prevalence"] = (
        value if (value := recurrence_prevalence(output)) is not None else UNAVAILABLE
    )
    result = build_cfdna_suitability(output, matrix=matrix, weights=weights)
    output["patient_coverage"] = (
        result["components"].get("patient_coverage", UNAVAILABLE)
    )
    output["cfdna_suitability"] = result["score"]
    output["cfdna_suitability_status"] = result["status"]
    output["cfdna_suitability_components"] = result["components"]
    return output
