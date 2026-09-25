from wgr_cdp.data_loader import validate_manifest

def test_manifest_schema():
    rows = [{
        "dataset_id":"test",
        "source":"test",
        "assay":"test",
        "genome_build":"GRCh38",
        "n_tumor":"0",
        "n_normal":"0",
        "stage_available":"unknown",
        "normal_type":"unknown",
        "access":"unknown",
        "license":"unknown",
        "notes":"test",
        "status":"partial",
    }]
    assert validate_manifest(rows) == []
