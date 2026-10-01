import pytest

from wgr_cdp.foundation_gate import validate_foundation_bundle
from wgr_cdp.status import CONDITIONAL, DATA_UNAVAILABLE


def _bundle():
    return {
        "dataset": {
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
            "notes": "fixture",
            "status": "partial",
        },
        "feature": {
            "patient": "P1",
            "region": "chr1:100",
            "feature_type": "SNV",
            "value": {"ref": "A", "alt": "G"},
            "status": DATA_UNAVAILABLE,
        },
        "provenance": {
            "source": "GDC",
            "source_file": "sample.vcf.gz",
            "source_record": "chr1:100:A:G",
            "genome_build": "GRCh38",
            "created_at": "2026-10-01T00:00:00+00:00",
            "run_id": "run-001",
        },
        "run": {
            "run_id": "run-001",
            "created_at": "2026-10-01T00:00:00+00:00",
            "config": {"seed": 42},
            "workflow_status": CONDITIONAL,
        },
        "trace": {
            "run_id": "run-001",
            "input_artifact_ids": ["in-1"],
            "output_artifact_ids": ["out-1"],
        },
        "input_artifact": {
            "artifact_id": "in-1",
            "path": "data/sample.vcf.gz",
            "artifact_type": "VCF",
            "status": DATA_UNAVAILABLE,
        },
        "output_artifact": {
            "artifact_id": "out-1",
            "path": "results/features.json",
            "artifact_type": "JSON",
            "workflow_status": CONDITIONAL,
            "schema_version": "A-10-1",
        },
    }


def test_valid_foundation_bundle_passes():
    result = validate_foundation_bundle(_bundle())
    assert result["run"]["run_id"] == "run-001"
    assert result["feature"]["status"] == DATA_UNAVAILABLE


def test_missing_section_rejected():
    bundle = _bundle()
    bundle.pop("trace")
    with pytest.raises(ValueError):
        validate_foundation_bundle(bundle)


def test_run_trace_mismatch_rejected():
    bundle = _bundle()
    bundle["trace"]["run_id"] = "run-002"
    with pytest.raises(ValueError):
        validate_foundation_bundle(bundle)


def test_unlinked_input_rejected():
    bundle = _bundle()
    bundle["trace"]["input_artifact_ids"] = []
    with pytest.raises(ValueError):
        validate_foundation_bundle(bundle)


def test_unlinked_output_rejected():
    bundle = _bundle()
    bundle["trace"]["output_artifact_ids"] = []
    with pytest.raises(ValueError):
        validate_foundation_bundle(bundle)


def test_invalid_feature_status_rejected():
    bundle = _bundle()
    bundle["feature"]["status"] = "negative"
    with pytest.raises(ValueError):
        validate_foundation_bundle(bundle)


def test_data_unavailable_remains_explicit():
    result = validate_foundation_bundle(_bundle())
    assert result["feature"]["status"] == "Data unavailable"
    assert result["input_artifact"]["status"] == "Data unavailable"
