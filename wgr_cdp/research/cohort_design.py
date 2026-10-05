"""C-12.4: explicit cohort design, batch and confounder metadata audit."""
from __future__ import annotations
from collections import defaultdict

UNAVAILABLE = "Data unavailable"

DESIGN_FIELDS = (
    "sequencing_platform",
    "sequencing_instrument",
    "coverage",
    "pipeline",
    "reference_build",
    "population",
    "batch",
    "library_prep",
    "sample_source",
)


def _value(row, field):
    aliases = {
        "sequencing_platform": ("sequencing_platform", "platform", "seq_platform"),
        "sequencing_instrument": ("sequencing_instrument", "instrument"),
        "coverage": ("coverage", "mean_depth", "median_depth"),
        "pipeline": ("pipeline", "analysis_pipeline", "workflow"),
        "reference_build": ("reference_build", "genome_build"),
        "population": ("population", "ancestry"),
        "batch": ("batch", "batch_id", "sequencing_batch"),
        "library_prep": ("library_prep", "library_preparation"),
        "sample_source": ("sample_source", "source", "tissue_source"),
    }
    for key in aliases[field]:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def _label(row):
    value = str(row.get("group") or "").strip().lower()
    if value in {"case", "cancer", "tumor"}:
        return "Cancer"
    if value in {"control", "healthy", "normal"}:
        return "Healthy"
    return UNAVAILABLE


def summarize_cohort_design(rows):
    """Summarize design metadata by group, preserving unavailable fields."""
    rows = list(rows or [])
    groups = {"Cancer": [r for r in rows if _label(r) == "Cancer"],
               "Healthy": [r for r in rows if _label(r) == "Healthy"]}
    fields = {}
    for field in DESIGN_FIELDS:
        by_group = {}
        for group, items in groups.items():
            observed = [_value(r, field) for r in items]
            observed = [v for v in observed if v not in (None, "")]
            by_group[group] = {
                "n_observed": len(observed),
                "n_missing": len(items) - len(observed),
                "unique_values": sorted({str(v) for v in observed}),
            }
        fields[field] = by_group
    return {
        "schema_version": "c12.cohort_design.v1",
        "status": "Available" if rows else UNAVAILABLE,
        "sample_count": len(rows),
        "group_counts": {group: len(items) for group, items in groups.items()},
        "fields": fields,
        "confounding_status": confounding_status(rows),
        "interpretation": (
            "Metadata balance is an audit signal. It does not by itself prove or "
            "exclude biological confounding."
        ),
    }


def confounding_status(rows):
    rows = list(rows or [])
    warnings = []
    for field in DESIGN_FIELDS:
        cancer = [str(_value(r, field)) for r in rows if _label(r) == "Cancer" and _value(r, field) not in (None, "")]
        healthy = [str(_value(r, field)) for r in rows if _label(r) == "Healthy" and _value(r, field) not in (None, "")]
        if not cancer or not healthy:
            warnings.append({
                "field": field,
                "status": UNAVAILABLE,
                "reason": "metadata_missing_in_one_or_both_groups",
            })
            continue
        if set(cancer).isdisjoint(set(healthy)):
            warnings.append({
                "field": field,
                "status": "Potential_confounding",
                "reason": "group_specific_values_do_not_overlap",
                "cancer_values": sorted(set(cancer)),
                "healthy_values": sorted(set(healthy)),
            })
        else:
            warnings.append({
                "field": field,
                "status": "No_obvious_group_specific_separation",
                "overlap_values": sorted(set(cancer) & set(healthy)),
            })
    return {"status": "Available", "fields": warnings}


def validate_cohort_design(rows):
    summary = summarize_cohort_design(rows)
    field_status = {item["field"]: item["status"] for item in summary["confounding_status"]["fields"]}
    hard_fail = [f for f, status in field_status.items() if status == "Potential_confounding"]
    return {
        "status": "FAIL" if hard_fail else summary["status"],
        "potential_confounders": hard_fail,
        "summary": summary,
        "scientific_boundary": (
            "A detected metadata imbalance is a review flag, not a claim that "
            "the corresponding biological result is invalid."
        ),
    }
