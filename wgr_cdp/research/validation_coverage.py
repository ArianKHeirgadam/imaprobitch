"""C-12.5: frozen-panel validation coverage across independent patient matrices."""
from __future__ import annotations

UNAVAILABLE = "Data unavailable"


def _coverage(matrix, selected):
    if not matrix or not selected:
        return None
    covered = 0
    observed = 0
    for patient, row in matrix.items():
        values = [row[c] for c in selected if c in row and row[c] in (0, 1)]
        if not values:
            continue
        observed += 1
        if any(values):
            covered += 1
    return covered / observed if observed else None


def compare_frozen_panel_coverage(discovery_presence, validation_presence, selected):
    """Evaluate the same frozen selected panel without re-optimization."""
    discovery = _coverage(discovery_presence, selected)
    validation = _coverage(validation_presence, selected)
    if discovery is None or validation is None:
        return {
            "schema_version": "c12.validation_coverage.v1",
            "status": UNAVAILABLE,
            "selected": list(selected),
            "discovery_coverage": discovery if discovery is not None else UNAVAILABLE,
            "validation_coverage": validation if validation is not None else UNAVAILABLE,
            "coverage_delta_validation_minus_discovery": UNAVAILABLE,
            "reoptimized": False,
        }
    return {
        "schema_version": "c12.validation_coverage.v1",
        "status": "Available",
        "selected": list(selected),
        "discovery_coverage": discovery,
        "validation_coverage": validation,
        "coverage_delta_validation_minus_discovery": validation - discovery,
        "reoptimized": False,
        "interpretation": (
            "Validation coverage is computed on the same frozen panel; no "
            "validation-cohort re-optimization is performed."
        ),
    }


def build_presence_matrix_from_rows(rows, patient_key="patient"):
    from .patient_coverage import build_presence_matrix
    return build_presence_matrix(rows, patient_key=patient_key, status_key="status")
