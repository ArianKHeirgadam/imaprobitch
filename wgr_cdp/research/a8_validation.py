"""A8: final empirical validation, leakage audit and reproducibility gate.

A8 is intentionally additive. It consumes discovery/A7 outputs and optional
independent validation data. Missing empirical inputs remain Data unavailable.
It never converts software-test success into a biological or clinical claim.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from random import Random

from .validation import AnalysisState, LeakageGuard


def _id(row):
    if isinstance(row, str):
        return row
    return str(row.get("candidate_id") or row.get("feature") or row.get("candidate") or "")


def _sample_id(row):
    if isinstance(row, str):
        return row
    for key in ("sample_id", "patient_id", "patient", "sample", "subject_id"):
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def audit_cohort_leakage(discovery_samples, validation_samples):
    """Audit sample/patient overlap without treating candidate overlap as leakage."""
    discovery = {str(x) for x in discovery_samples if x not in (None, "")}
    validation = {str(x) for x in validation_samples if x not in (None, "")}
    overlap = sorted(discovery & validation)
    return {
        "status": "FAIL" if overlap else ("Available" if discovery and validation else "Data unavailable"),
        "discovery_n": len(discovery),
        "validation_n": len(validation),
        "overlap_n": len(overlap),
        "overlap_ids": overlap,
        "leakage_free": bool(discovery and validation and not overlap),
    }


def audit_candidate_table_leakage(discovery_rows, validation_rows):
    """Check sample IDs when present; candidate IDs may legitimately replicate."""
    d = [_sample_id(x) for x in discovery_rows]
    v = [_sample_id(x) for x in validation_rows]
    if not any(d) or not any(v):
        return {
            "status": "Data unavailable",
            "reason": "sample_or_patient_ids_required_for_empirical_leakage_audit",
            "leakage_free": None,
        }
    return audit_cohort_leakage(d, v)


def validate_state_transition():
    """Exercise the required DISCOVERY -> FROZEN -> VALIDATION transition."""
    guard = LeakageGuard()
    initial = guard.state.value
    guard.freeze()
    frozen = guard.state.value
    guard.enter_validation()
    final = guard.state.value
    return {
        "status": "Available",
        "initial": initial,
        "frozen": frozen,
        "validation": final,
        "valid_transition": (
            initial == AnalysisState.DISCOVERY.value
            and frozen == AnalysisState.FROZEN.value
            and final == AnalysisState.VALIDATION.value
        ),
    }


def revalidate_selected(selected_ids, validation_rows):
    """Check discovery-selected candidates against an independent candidate table."""
    selected = {str(x) for x in selected_ids if x not in (None, "")}
    if validation_rows is None:
        return {
            "status": "Data unavailable",
            "selected_n": len(selected),
            "revalidated_n": 0,
            "revalidation_rate": None,
            "revalidated_candidates": [],
        }

    validation_ids = {_id(row) for row in validation_rows if _id(row)}
    found = sorted(selected & validation_ids)
    return {
        "status": "Available",
        "selected_n": len(selected),
        "validation_candidate_n": len(validation_ids),
        "revalidated_n": len(found),
        "revalidation_rate": len(found) / len(selected) if selected else None,
        "revalidated_candidates": found,
    }


def generalization_summary(discovery_rows, validation_rows, candidate_ids=None):
    """Compare replicated candidate evidence without inventing missing values."""
    if discovery_rows is None or validation_rows is None:
        return {"status": "Data unavailable", "candidates": []}

    d = {_id(row): row for row in discovery_rows if _id(row)}
    v = {_id(row): row for row in validation_rows if _id(row)}
    ids = sorted(set(candidate_ids or d.keys()) & set(v.keys()))
    if not ids:
        return {"status": "Data unavailable", "candidates": [], "reason": "no_replicated_candidates"}

    records = []
    concordant = 0
    effect_available = 0
    for cid in ids:
        dr, vr = d[cid], v[cid]
        de = _float(dr.get("effect_size", dr.get("frequency_difference")))
        ve = _float(vr.get("effect_size", vr.get("frequency_difference")))
        dp = _float(dr.get("p_value"))
        dq = _float(dr.get("q_value"))
        vp = _float(vr.get("p_value"))
        vq = _float(vr.get("q_value"))
        direction = None
        if de is not None and ve is not None:
            effect_available += 1
            direction = "concordant" if (de == 0 and ve == 0) or (de * ve > 0) else "discordant"
            if direction == "concordant":
                concordant += 1
        records.append({
            "candidate_id": cid,
            "discovery_effect": de if de is not None else "Data unavailable",
            "validation_effect": ve if ve is not None else "Data unavailable",
            "effect_direction": direction or "Data unavailable",
            "discovery_p_value": dp if dp is not None else "Data unavailable",
            "discovery_q_value": dq if dq is not None else "Data unavailable",
            "validation_p_value": vp if vp is not None else "Data unavailable",
            "validation_q_value": vq if vq is not None else "Data unavailable",
        })

    return {
        "status": "Available",
        "candidate_n": len(records),
        "effect_direction_concordance": (
            concordant / effect_available if effect_available else "Data unavailable"
        ),
        "effect_pairs_available": effect_available,
        "candidates": records,
    }


def bootstrap_validation_revalidation(selected_ids, validation_rows, n_bootstrap=200, seed=42):
    """Bootstrap validation rows and report revalidation-rate stability."""
    if validation_rows is None or not validation_rows:
        return {"status": "Data unavailable", "n_bootstrap": 0, "revalidation_rate": None}

    selected = {str(x) for x in selected_ids if x not in (None, "")}
    if not selected:
        return {"status": "Available", "n_bootstrap": int(n_bootstrap), "revalidation_rate": None}

    rng = Random(seed)
    rates = []
    rows = list(validation_rows)
    for _ in range(int(n_bootstrap)):
        sample = [rows[rng.randrange(len(rows))] for _ in rows]
        ids = {_id(row) for row in sample if _id(row)}
        rates.append(len(selected & ids) / len(selected))

    return {
        "status": "Available",
        "n_bootstrap": int(n_bootstrap),
        "seed": int(seed),
        "revalidation_rate": sum(rates) / len(rates),
        "min_rate": min(rates),
        "max_rate": max(rates),
    }


def build_quality_gate(
    leakage,
    independent_validation_available,
    revalidation,
    generalization,
    reproducibility=None,
):
    """Return a transparent final gate; PASS requires empirical validation inputs."""
    criteria = {
        "leakage_free": bool(leakage.get("leakage_free")) if leakage.get("status") != "Data unavailable" else None,
        "independent_validation": bool(independent_validation_available),
        "revalidation_available": revalidation.get("status") == "Available",
        "generalization_available": generalization.get("status") == "Available",
        "reproducibility": (
            bool(reproducibility.get("valid_transition"))
            if reproducibility is not None else None
        ),
    }

    if criteria["leakage_free"] is False:
        overall = "FAIL"
    elif not criteria["independent_validation"] or not criteria["revalidation_available"]:
        overall = "CONDITIONAL"
    elif criteria["leakage_free"] is None:
        overall = "CONDITIONAL"
    elif reproducibility is not None and criteria["reproducibility"] is False:
        overall = "FAIL"
    else:
        overall = "PASS"

    return {
        "overall": overall,
        "criteria": criteria,
        "interpretation": (
            "PASS means the supplied independent validation inputs passed the software gate; "
            "it does not establish clinical utility or prospective diagnostic performance."
        ),
    }


def run_a8(
    selected_ids,
    discovery_rows=None,
    validation_rows=None,
    discovery_samples=None,
    validation_samples=None,
    n_bootstrap=200,
    seed=42,
):
    """Run the complete A8 validation and quality-gate record."""
    discovery_rows = list(discovery_rows or [])
    validation_rows = None if validation_rows is None else list(validation_rows)

    if discovery_samples is None:
        discovery_samples = [_sample_id(row) for row in discovery_rows]
    if validation_samples is None and validation_rows is not None:
        validation_samples = [_sample_id(row) for row in validation_rows]

    if discovery_samples is None or validation_samples is None:
        leakage = {
            "status": "Data unavailable",
            "reason": "independent_sample_ids_required",
            "leakage_free": None,
        }
    else:
        leakage = audit_cohort_leakage(discovery_samples, validation_samples)

    state = validate_state_transition()
    revalidation = revalidate_selected(selected_ids, validation_rows)
    generalization = generalization_summary(
        discovery_rows,
        validation_rows,
        candidate_ids=selected_ids,
    )
    bootstrap = bootstrap_validation_revalidation(
        selected_ids,
        validation_rows,
        n_bootstrap=n_bootstrap,
        seed=seed,
    )
    gate = build_quality_gate(
        leakage=leakage,
        independent_validation_available=bool(validation_rows),
        revalidation=revalidation,
        generalization=generalization,
        reproducibility=state,
    )
    return {
        "status": "Available" if validation_rows else "Data unavailable",
        "selected": [str(x) for x in selected_ids],
        "leakage_audit": leakage,
        "state_audit": state,
        "revalidation": revalidation,
        "generalization": generalization,
        "bootstrap_stability": bootstrap,
        "quality_gate": gate,
    }


def write_a8_artifacts(output_dir, result):
    """Persist machine-readable A8 artifacts without modifying A0-A7 artifacts."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    names = {
        "a8_validation.json": result,
        "a8_leakage_audit.json": result.get("leakage_audit", {}),
        "a8_bootstrap_stability.json": result.get("bootstrap_stability", {}),
        "a8_generalization.json": result.get("generalization", {}),
        "a8_quality_gate.json": result.get("quality_gate", {}),
    }
    for name, payload in names.items():
        (output / name).write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )

    rows = result.get("generalization", {}).get("candidates", [])
    with (output / "a8_generalization.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "candidate_id", "discovery_effect", "validation_effect",
            "effect_direction", "discovery_p_value", "discovery_q_value",
            "validation_p_value", "validation_q_value",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return {
        "directory": str(output),
        "artifacts": sorted(names) + ["a8_generalization.csv"],
    }


def append_a8_to_report(output_dir, result):
    """Append an A8 quality-gate section to the existing HTML report."""
    report = Path(output_dir) / "report.html"
    if not report.exists():
        return False

    import html

    gate = result.get("quality_gate", {})
    section = (
        "<hr><h2>Final A8 Empirical Validation Gate</h2>"
        "<p>A8 reports independent-validation and leakage status only; it is not a clinical validation claim.</p>"
        f"<ul><li>Quality gate: <strong>{html.escape(str(gate.get('overall', 'Data unavailable')))}</strong></li>"
        f"<li>Leakage audit: {html.escape(str(result.get('leakage_audit', {}).get('status', 'Data unavailable')))}</li>"
        f"<li>Revalidation: {html.escape(str(result.get('revalidation', {}).get('status', 'Data unavailable')))}</li>"
        f"<li>Generalization: {html.escape(str(result.get('generalization', {}).get('status', 'Data unavailable')))}</li></ul>"
        "<p>Machine-readable A8 artifacts: <code>a8_validation.json</code>, "
        "<code>a8_leakage_audit.json</code>, <code>a8_bootstrap_stability.json</code>, "
        "<code>a8_generalization.json</code>, <code>a8_generalization.csv</code>, "
        "<code>a8_quality_gate.json</code>.</p>"
    )
    document = report.read_text(encoding="utf-8")
    marker = "</body>"
    document = document.replace(marker, section + marker, 1) if marker in document else document + section
    report.write_text(document, encoding="utf-8")
    return True
