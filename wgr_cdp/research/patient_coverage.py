"""C-12.2: formal patient-level presence/absence coverage algorithms.

This module is separate from probabilistic detectability coverage. Presence is
based only on explicit Detected/Not detected observations, while
"Data unavailable" remains excluded from the denominator.
"""
from __future__ import annotations

from itertools import combinations
import math

UNAVAILABLE = "Data unavailable"


def candidate_key(row):
    return str(row.get("candidate_id") or row.get("feature") or row.get("candidate") or "")


def build_presence_matrix(rows, patient_key="patient", status_key="status"):
    """Build patient x candidate binary matrix from explicit observations."""
    patients = sorted({str(row.get(patient_key)) for row in rows if row.get(patient_key) not in (None, "")})
    candidates = sorted({candidate_key(row) for row in rows if candidate_key(row)})
    matrix = {patient: {} for patient in patients}
    for row in rows:
        patient = str(row.get(patient_key) or "")
        candidate = candidate_key(row)
        if not patient or not candidate:
            continue
        status = str(row.get(status_key) or "").strip().lower()
        if status in {"detected", "present", "positive", "1", "true"}:
            matrix[patient][candidate] = 1
        elif status in {"not detected", "absent", "negative", "0", "false"}:
            matrix[patient][candidate] = 0
    return {
        "patients": patients,
        "candidates": candidates,
        "matrix": matrix,
        "status": "Available" if patients and candidates else UNAVAILABLE,
    }


def panel_presence_coverage(matrix, selected):
    if not matrix or not selected:
        return {
            "status": "Available",
            "coverage": 0.0,
            "covered_patient_count": 0,
            "observed_patient_count": 0,
            "covered_patients": [],
        }
    covered = []
    observed = []
    for patient in sorted(matrix):
        row = matrix.get(patient) or {}
        values = [row[c] for c in selected if c in row and row[c] in (0, 1)]
        if not values:
            continue
        observed.append(patient)
        if any(values):
            covered.append(patient)
    return {
        "status": "Available" if observed else UNAVAILABLE,
        "coverage": len(covered) / len(observed) if observed else None,
        "covered_patient_count": len(covered),
        "observed_patient_count": len(observed),
        "covered_patients": covered,
    }


def greedy_presence_panel(matrix, max_k=15, min_gain=0.02):
    max_k = min(15, max(0, int(max_k)))
    gain_threshold = max(0.0, float(min_gain))
    candidates = sorted({c for row in matrix.values() for c, v in row.items() if v in (0, 1)})
    selected = []
    previous = 0.0
    while candidates and len(selected) < max_k:
        scores = []
        for candidate in candidates:
            result = panel_presence_coverage(matrix, selected + [candidate])
            scores.append((result["coverage"] or 0.0, candidate, result))
        best_coverage, best, result = max(scores, key=lambda item: (item[0], item[1]))
        gain = best_coverage - previous
        if selected and gain < gain_threshold:
            break
        selected.append(best)
        candidates.remove(best)
        previous = best_coverage
    return {
        "status": "Available",
        "method": "greedy_presence",
        "selected": selected,
        "coverage": previous,
        "k": len(selected),
    }


def exact_presence_panel(matrix, max_k=15, min_gain=0.0, max_candidates=22):
    max_k = min(15, max(0, int(max_k)))
    min_gain = max(0.0, float(min_gain))
    candidates = sorted({c for row in matrix.values() for c, v in row.items() if v in (0, 1)})
    if len(candidates) > max_candidates:
        return {
            "status": "not_run",
            "method": "exact_presence",
            "selected": [],
            "coverage": 0.0,
            "reason": "too_many_candidates",
        }
    best = (0.0, ())
    for k in range(1, min(max_k, len(candidates)) + 1):
        for combo in combinations(candidates, k):
            coverage = panel_presence_coverage(matrix, combo)["coverage"] or 0.0
            if coverage > best[0] + max(min_gain if k > 1 else 0.0, 1e-12):
                best = (coverage, combo)
    return {
        "status": "Available",
        "method": "exact_presence",
        "selected": list(best[1]),
        "coverage": best[0],
        "k": len(best[1]),
    }


def write_presence_matrix(path, payload):
    import csv
    from pathlib import Path
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    patients = payload["patients"]
    candidates = payload["candidates"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["patient"] + candidates)
        writer.writeheader()
        for patient in patients:
            row = {"patient": patient}
            row.update({c: payload["matrix"].get(patient, {}).get(c, UNAVAILABLE) for c in candidates})
            writer.writerow(row)
    return path
