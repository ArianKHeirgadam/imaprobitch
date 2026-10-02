import pytest

from wgr_cdp.exact_scanner_normalization import (
    deduplicate_scanner_inputs,
    normalize_feature_record,
    normalize_scanner_inputs,
)


def test_normalize_strips_identity_fields():
    result = normalize_feature_record(
        {
            "patient": " P1 ",
            "region": " chr1:100 ",
            "value": 1,
            "feature_type": " SNV ",
        }
    )
    assert result["patient"] == "P1"
    assert result["region"] == "chr1:100"
    assert result["feature_type"] == "SNV"


@pytest.mark.parametrize("field", ["patient", "region", "value"])
def test_required_field_is_enforced(field):
    payload = {"patient": "P1", "region": "chr1:100", "value": 1}
    payload.pop(field)
    with pytest.raises(ValueError):
        normalize_feature_record(payload)


@pytest.mark.parametrize("field", ["patient", "region"])
def test_blank_identity_field_is_rejected(field):
    payload = {"patient": "P1", "region": "chr1:100", "value": 1}
    payload[field] = "   "
    with pytest.raises(ValueError):
        normalize_feature_record(payload)


def test_normalize_preserves_value():
    value = {"ref": "A", "alt": "G", "vaf": 0.12}
    result = normalize_feature_record(
        {"patient": "P1", "region": "chr1:100", "value": value}
    )
    assert result["value"] == value


def test_collection_preserves_order():
    result = normalize_scanner_inputs(
        [
            {"patient": "P2", "region": "chr2:10", "value": 1},
            {"patient": "P1", "region": "chr1:10", "value": 2},
        ]
    )
    assert [row["patient"] for row in result] == ["P2", "P1"]


def test_exact_duplicates_are_removed():
    records = [
        {"patient": "P1", "region": "chr1:10", "value": 1},
        {"patient": "P1", "region": "chr1:10", "value": 1},
        {"patient": "P2", "region": "chr1:10", "value": 1},
    ]
    result = deduplicate_scanner_inputs(records)
    assert len(result) == 2
    assert result[0]["patient"] == "P1"
    assert result[1]["patient"] == "P2"


def test_same_region_different_patient_is_not_duplicate():
    records = [
        {"patient": "P1", "region": "chr1:10", "value": 1},
        {"patient": "P2", "region": "chr1:10", "value": 1},
    ]
    assert len(deduplicate_scanner_inputs(records)) == 2


def test_same_region_different_value_is_not_duplicate():
    records = [
        {"patient": "P1", "region": "chr1:10", "value": 1},
        {"patient": "P1", "region": "chr1:10", "value": 2},
    ]
    assert len(deduplicate_scanner_inputs(records)) == 2


def test_same_measurement_with_different_feature_type_is_not_merged():
    records = [
        {"patient": "P1", "region": "chr1:10", "value": 1, "feature_type": "SNV"},
        {"patient": "P1", "region": "chr1:10", "value": 1, "feature_type": "CNV"},
    ]
    result = deduplicate_scanner_inputs(records)
    assert len(result) == 2
    assert [row["feature_type"] for row in result] == ["SNV", "CNV"]


def test_same_measurement_with_different_status_is_not_merged():
    records = [
        {"patient": "P1", "region": "chr1:10", "value": 1, "status": "Detected"},
        {"patient": "P1", "region": "chr1:10", "value": 1, "status": "Data unavailable"},
    ]
    assert len(deduplicate_scanner_inputs(records)) == 2


def test_nested_mapping_order_does_not_change_duplicate_identity():
    records = [
        {"patient": "P1", "region": "chr1:10", "value": {"ref": "A", "alt": "G"}},
        {"patient": "P1", "region": "chr1:10", "value": {"alt": "G", "ref": "A"}},
    ]
    assert len(deduplicate_scanner_inputs(records)) == 1


def test_normalization_canonicalizes_feature_type_and_group():
    result = normalize_feature_record(
        {
            "patient": "P1",
            "region": "chr1:10",
            "value": 1,
            "feature_type": " snv ",
            "group": " Cancer ",
        }
    )
    assert result["feature_type"] == "SNV"
    assert result["group"] == "cancer"


def test_non_finite_values_are_rejected_during_deduplication():
    records = [{"patient": "P1", "region": "chr1:10", "value": float("nan")}]
    with pytest.raises(ValueError, match="JSON-compatible finite values"):
        deduplicate_scanner_inputs(records)
