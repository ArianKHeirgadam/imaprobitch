import pytest

from wgr_cdp.artifact_contract import (
    InputArtifact,
    OutputArtifact,
    validate_input_artifact,
    validate_output_artifact,
)
from wgr_cdp.status import DATA_UNAVAILABLE, PASS


def test_input_artifact_defaults_to_data_unavailable():
    artifact = InputArtifact("in-1", "data/a.vcf", "VCF")
    assert artifact.status == DATA_UNAVAILABLE


def test_input_artifact_round_trip():
    artifact = InputArtifact("in-1", "data/a.vcf", "VCF", checksum="abc")
    assert artifact.to_dict()["checksum"] == "abc"


def test_input_validation_requires_identity_fields():
    with pytest.raises(ValueError):
        validate_input_artifact({"path": "data/a.vcf", "artifact_type": "VCF"})


def test_input_validation_defaults_status():
    result = validate_input_artifact(
        {"artifact_id": "in-1", "path": "x", "artifact_type": "VCF"}
    )
    assert result["status"] == DATA_UNAVAILABLE


def test_output_artifact_requires_workflow_status():
    artifact = OutputArtifact("out-1", "results/a.json", "JSON", PASS, "A7-1")
    assert artifact.to_dict()["workflow_status"] == PASS


def test_output_validation_requires_schema_version():
    with pytest.raises(ValueError):
        validate_output_artifact(
            {
                "artifact_id": "out-1",
                "path": "results/a.json",
                "artifact_type": "JSON",
                "workflow_status": PASS,
            }
        )


def test_output_validation_rejects_feature_status_as_workflow_status():
    with pytest.raises(ValueError):
        validate_output_artifact(
            {
                "artifact_id": "out-1",
                "path": "results/a.json",
                "artifact_type": "JSON",
                "workflow_status": DATA_UNAVAILABLE,
                "schema_version": "A7-1",
            }
        )


def test_output_round_trip():
    artifact = OutputArtifact("out-1", "results/a.json", "JSON", PASS, "A7-1")
    assert validate_output_artifact(artifact.to_dict()) == artifact.to_dict()
