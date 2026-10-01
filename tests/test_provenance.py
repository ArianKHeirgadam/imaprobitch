import pytest

from wgr_cdp.provenance import (
    REQUIRED_PROVENANCE_FIELDS,
    Provenance,
    provenance_from_mapping,
    validate_provenance,
)


def _valid():
    return {
        "source": "GDC",
        "source_file": "sample.vcf.gz",
        "source_record": "chr1:100:A:G",
        "genome_build": "GRCh38",
        "created_at": "2026-10-01T00:00:00+00:00",
        "run_id": "run-001",
    }


def test_required_provenance_fields_are_exact():
    assert REQUIRED_PROVENANCE_FIELDS == {
        "source",
        "source_file",
        "source_record",
        "genome_build",
        "created_at",
        "run_id",
    }


def test_provenance_validates_and_round_trips():
    p = Provenance(**_valid())
    assert p.to_dict() == _valid()


def test_mapping_validation_preserves_values():
    assert validate_provenance(_valid()) == _valid()


def test_missing_provenance_field_rejected():
    payload = _valid()
    payload.pop("run_id")
    with pytest.raises(ValueError):
        validate_provenance(payload)


@pytest.mark.parametrize("field", sorted(REQUIRED_PROVENANCE_FIELDS))
def test_blank_provenance_field_rejected(field):
    payload = _valid()
    payload[field] = ""
    with pytest.raises(ValueError):
        validate_provenance(payload)


def test_mapping_builds_typed_provenance():
    p = provenance_from_mapping(_valid())
    assert isinstance(p, Provenance)
    assert p.genome_build == "GRCh38"


def test_extra_metadata_is_allowed():
    payload = _valid()
    payload["workflow"] = "WGR-CDP"
    result = validate_provenance(payload)
    assert result["workflow"] == "WGR-CDP"
