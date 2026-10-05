from wgr_cdp.research.cnv_statistics import describe_cnv_statistics, permutation_mean_p_value
from wgr_cdp.research.cohort_design import summarize_cohort_design, validate_cohort_design
from wgr_cdp.research.external_evidence import evidence_hierarchy, classify_external_evidence
from wgr_cdp.research.confidence import evidence_strength_confidence


def test_cnv_statistics_is_reproducible():
    a = permutation_mean_p_value([2, 3, 2], [0, 0, 1], permutations=100, seed=7)
    b = permutation_mean_p_value([2, 3, 2], [0, 0, 1], permutations=100, seed=7)
    assert a == b
    assert 0 <= a <= 1
    assert describe_cnv_statistics([2, 3], [0, 1])["statistical_test"] == "permutation_test_mean_difference"


def test_cohort_design_reports_missing_and_group_specific_metadata():
    rows = [
        {"group": "case", "platform": "A", "batch": "C1"},
        {"group": "control", "platform": "B", "batch": "H1"},
    ]
    summary = summarize_cohort_design(rows)
    assert summary["schema_version"] == "c12.cohort_design.v1"
    assert "sequencing_platform" in summary["fields"]
    result = validate_cohort_design(rows)
    assert "sequencing_platform" in result["potential_confounders"]


def test_external_evidence_hierarchy_is_typed():
    hierarchy = evidence_hierarchy()
    assert hierarchy["schema_version"] == "c12.evidence_hierarchy.v1"
    assert [x["category"] for x in hierarchy["tiers"]][:3] == [
        "functional", "population_identity", "clinical"
    ]
    row = {
        "annotation": {"dbsnp_rsids": ["rs1"], "clinvar_accession": "A1"},
        "functional_evidence": {"consequence": "missense_variant"},
        "cancer_evidence_score": "0.8",
        "prior_cfdna_evidence": "0.7",
    }
    out = classify_external_evidence(row)
    assert out["functional"]["available"]
    assert out["population_identity"]["available"]
    assert out["clinical"]["available"]


def test_confidence_is_evidence_strength_not_probability():
    row = {
        "research_score": 0.82,
        "score_fields": ["statistical_strength", "detectability", "recurrence_prevalence",
                         "cfdna_suitability", "patient_coverage"],
    }
    out = evidence_strength_confidence(row, stability=0.9)
    assert out["level"] == "HIGH"
    assert "probability" in out["meaning"] and "not probability" in out["meaning"]
    assert out["validation_status"] == "Data unavailable"
