import pytest

from wgr_cdp.dataset_manifest import (
    REQUIRED_DATASET_FIELDS,
    VALID_DATASET_STATUSES,
    validate_dataset_manifest,
)


def _valid():
    return {
        "dataset_id": "TCGA-STAD",
        "source": "GDC",
        "assay": "WGS",
        "genome_build": "GRCh38",
        "n_tumor": 10,
        "n_normal": 10,
        "stage_available": True,
        "normal_type": "solid_tissue_normal",
        "access": "open",
        "license": "GDC",
        "notes": "metadata only",
        "status": "partial",
    }


def test_required_fields_match_manifest_contract():
    assert REQUIRED_DATASET_FIELDS == {
        "dataset_id", "source", "assay", "genome_build",
        "n_tumor", "n_normal", "stage_available", "normal_type",
        "access", "license", "notes", "status",
    }


def test_valid_manifest_is_accepted():
    result = validate_dataset_manifest(_valid())
    assert result == _valid()


def test_all_documented_statuses_are_valid():
    for status in VALID_DATASET_STATUSES:
        payload = _valid()
        payload["status"] = status
        assert validate_dataset_manifest(payload)["status"] == status


def test_missing_required_field_is_rejected():
    payload = _valid()
    payload.pop("genome_build")
    with pytest.raises(ValueError):
        validate_dataset_manifest(payload)


@pytest.mark.parametrize("field", ["dataset_id", "source", "assay", "genome_build", "access", "license"])
def test_blank_identity_field_is_rejected(field):
    payload = _valid()
    payload[field] = ""
    with pytest.raises(ValueError):
        validate_dataset_manifest(payload)


def test_invalid_status_is_rejected():
    payload = _valid()
    payload["status"] = "available"
    with pytest.raises(ValueError):
        validate_dataset_manifest(payload)


@pytest.mark.parametrize("field", ["n_tumor", "n_normal"])
def test_sample_counts_must_be_non_negative_integers(field):
    payload = _valid()
    payload[field] = -1
    with pytest.raises(ValueError):
        validate_dataset_manifest(payload)


@pytest.mark.parametrize("field", ["n_tumor", "n_normal"])
def test_boolean_is_not_a_sample_count(field):
    payload = _valid()
    payload[field] = True
    with pytest.raises(ValueError):
        validate_dataset_manifest(payload)


def test_stage_available_must_be_boolean():
    payload = _valid()
    payload["stage_available"] = "yes"
    with pytest.raises(ValueError):
        validate_dataset_manifest(payload)


def test_notes_must_be_string():
    payload = _valid()
    payload["notes"] = None
    with pytest.raises(ValueError):
        validate_dataset_manifest(payload)


def test_extra_metadata_is_preserved():
    payload = _valid()
    payload["dataset_version"] = "release-43"
    result = validate_dataset_manifest(payload)
    assert result["dataset_version"] == "release-43"
