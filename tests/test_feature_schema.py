import pytest

from wgr_cdp.feature_schema import (
    REQUIRED_FEATURE_FIELDS,
    FeatureRecord,
    feature_record_from_mapping,
    validate_feature_schema,
)
from wgr_cdp.status import DATA_UNAVAILABLE, DETECTED


def test_required_common_feature_fields():
    assert REQUIRED_FEATURE_FIELDS == {
        "patient",
        "region",
        "feature_type",
        "value",
        "status",
    }


def test_feature_record_defaults_missing_optional_fields():
    record = FeatureRecord(
        patient="P1",
        region="chr1:100",
        feature_type="SNV",
        value={"ref": "A", "alt": "G"},
    )
    assert record.status == DATA_UNAVAILABLE
    assert record.gene is None
    assert record.sample is None


def test_feature_record_round_trips_to_dict():
    record = FeatureRecord(
        patient="P1",
        region="chr1:100",
        feature_type="SNV",
        value={"ref": "A", "alt": "G"},
        status=DETECTED,
        gene="GENE1",
        provenance={"source": "fixture.vcf", "genome_build": "GRCh38"},
    )
    payload = record.to_dict()
    assert payload["patient"] == "P1"
    assert payload["region"] == "chr1:100"
    assert payload["feature_type"] == "SNV"
    assert payload["status"] == DETECTED
    assert payload["provenance"]["genome_build"] == "GRCh38"


def test_mapping_schema_validation():
    payload = {
        "patient": "P1",
        "region": "chr1:100",
        "feature_type": "CNV",
        "value": 0.8,
        "status": DATA_UNAVAILABLE,
    }
    assert validate_feature_schema(payload) == payload


@pytest.mark.parametrize(
    "payload",
    [
        {"region": "chr1:100", "feature_type": "SNV", "value": 1, "status": DETECTED},
        {"patient": "P1", "feature_type": "SNV", "value": 1, "status": DETECTED},
        {"patient": "P1", "region": "chr1:100", "value": 1, "status": DETECTED},
        {"patient": "P1", "region": "chr1:100", "feature_type": "SNV", "status": DETECTED},
    ],
)
def test_missing_required_field_rejected(payload):
    with pytest.raises(ValueError):
        validate_feature_schema(payload)


def test_blank_identity_field_rejected():
    with pytest.raises(ValueError):
        FeatureRecord(
            patient="",
            region="chr1:100",
            feature_type="SNV",
            value=1,
            status=DETECTED,
        )


def test_invalid_status_rejected():
    with pytest.raises(ValueError):
        FeatureRecord(
            patient="P1",
            region="chr1:100",
            feature_type="SNV",
            value=1,
            status="unavailable",
        )


def test_mapping_builds_typed_record():
    record = feature_record_from_mapping(
        {
            "patient": "P1",
            "region": "chr1:100",
            "feature_type": "METHYLATION",
            "value": 0.72,
            "status": DETECTED,
        }
    )
    assert isinstance(record, FeatureRecord)
    assert record.feature_type == "METHYLATION"
