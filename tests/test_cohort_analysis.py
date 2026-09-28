import math

import pytest

from wgr_cdp.cohort_analysis import (
    compare_gene_cohorts,
    compare_variant_cohorts,
    fisher_exact_2x2,
    normalize_cohort,
)


def test_normalize_cohort_deduplicates_within_sample():
    result = normalize_cohort([{
        "sample_id": "S1",
        "group": "case",
        "variants": ["v1", "v1", "v2"],
    }])

    assert result[0]["variants"] == ["v1", "v2"]


def test_normalize_cohort_preserves_variant_records():
    records = [{"gene": "TP53", "consequence": "missense_variant"}]

    result = normalize_cohort([{
        "sample_id": "S1",
        "group": "case",
        "variants": ["v1"],
        "variant_records": records,
    }])

    assert result[0]["variant_records"] == records


def test_variant_cohort_comparison_calculates_frequencies_and_effect():
    samples = [
        {"sample_id": "C1", "group": "case", "variants": ["v1", "v2"]},
        {"sample_id": "C2", "group": "case", "variants": ["v1"]},
        {"sample_id": "H1", "group": "control", "variants": ["v2"]},
        {"sample_id": "H2", "group": "control", "variants": []},
    ]

    results = compare_variant_cohorts(samples)
    by_feature = {row["feature"]: row for row in results}

    assert by_feature["v1"]["case_frequency"] == 1.0
    assert by_feature["v1"]["control_frequency"] == 0.0
    assert math.isinf(by_feature["v1"]["case_control_frequency_ratio"])
    assert by_feature["v2"]["case_frequency"] == 0.5
    assert by_feature["v2"]["control_frequency"] == 0.5
    assert by_feature["v2"]["frequency_difference"] == 0.0


def test_fisher_exact_returns_expected_boundary_values():
    assert fisher_exact_2x2(0, 0, 2, 2) == 1.0
    assert fisher_exact_2x2(2, 0, 0, 2) == pytest.approx(1 / 3)


def test_gene_cohort_comparison_uses_gene_carriers():
    samples = [
        {
            "sample_id": "C1",
            "group": "case",
            "variants": ["v1"],
            "variant_records": [{"gene": "TP53"}],
        },
        {
            "sample_id": "C2",
            "group": "case",
            "variants": ["v2"],
            "variant_records": [{"gene": "TP53"}],
        },
        {
            "sample_id": "H1",
            "group": "control",
            "variants": [],
            "variant_records": [],
        },
    ]

    results = compare_gene_cohorts(samples)

    assert results[0]["feature"] == "TP53"
    assert results[0]["case_carriers"] == 2
    assert results[0]["control_carriers"] == 0
    assert results[0]["case_frequency"] == 1.0


def test_cohort_comparison_requires_both_groups():
    with pytest.raises(ValueError):
        compare_variant_cohorts([{
            "sample_id": "C1",
            "group": "case",
            "variants": ["v1"],
        }])
