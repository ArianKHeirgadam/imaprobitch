from wgr_cdp.research.cfdna_prioritization import (
    build_cfdna_suitability, augment_candidate, recurrence_prevalence,
)
from wgr_cdp.research.patient_coverage import (
    build_presence_matrix, panel_presence_coverage, greedy_presence_panel,
)


def test_recurrence_uses_observed_case_prevalence():
    assert recurrence_prevalence({"case_carriers": 4, "case_n": 10}) == 0.4


def test_cfdna_suitability_is_missingness_aware():
    row = {
        "candidate_id": "A",
        "case_frequency": 0.5,
        "detectability": 0.8,
        "clonality": "Data unavailable",
        "allele_fraction": 0.2,
        "mappability": 0.99,
        "prior_cfdna_evidence": 0.7,
        "alteration_type_support": "Data unavailable",
    }
    out = build_cfdna_suitability(row)
    assert out["status"] == "Available"
    assert set(out["used_components"]) == {
        "detectability", "recurrence_prevalence", "allele_fraction",
        "mappability", "prior_cfdna_evidence",
    }
    assert 0 <= out["score"] <= 1


def test_cfDNA_augmentation_does_not_mutate():
    row = {"candidate_id": "A", "case_frequency": 0.4}
    out = augment_candidate(row)
    assert "cfdna_suitability" in out
    assert "cfdna_suitability" not in row


def test_presence_matrix_explicit_statuses():
    rows = [
        {"patient": "P1", "feature": "A", "status": "Detected"},
        {"patient": "P1", "feature": "B", "status": "Not detected"},
        {"patient": "P2", "feature": "A", "status": "Not detected"},
        {"patient": "P2", "feature": "B", "status": "Detected"},
    ]
    out = build_presence_matrix(rows)
    assert out["matrix"]["P1"]["A"] == 1
    assert out["matrix"]["P1"]["B"] == 0
    assert out["matrix"]["P2"]["B"] == 1


def test_panel_presence_coverage_and_greedy():
    matrix = {
        "P1": {"A": 1, "B": 0, "C": 0},
        "P2": {"A": 0, "B": 1, "C": 0},
        "P3": {"A": 0, "B": 0, "C": 1},
    }
    summary = panel_presence_coverage(matrix, ["A", "B", "C"])
    assert summary["coverage"] == 1.0
    panel = greedy_presence_panel(matrix, max_k=2, min_gain=0)
    assert set(panel["selected"]) in ({"A", "B"}, {"A", "C"}, {"B", "C"})


def test_presence_missing_values_are_not_negative_evidence():
    matrix = {
        "P1": {"A": 1},
        "P2": {"A": "Data unavailable"},
        "P3": {},
    }
    summary = panel_presence_coverage(matrix, ["A"])
    assert summary["covered_patient_count"] == 1
    assert summary["observed_patient_count"] == 1
    assert summary["coverage"] == 1.0
