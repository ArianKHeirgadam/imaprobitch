import json
from wgr_cdp.data_ingestion import gdc_cohort as c


def test_classify_sample_uses_explicit_metadata():
    assert c.classify_sample({"sample_type": "Primary Tumor"}) == "TUMOR"
    assert c.classify_sample({"sample_type": "Solid Tissue Normal"}) == "NORMAL"
    assert c.classify_sample({"sample_type": "Metastatic"}) == "TUMOR_METASTATIC"
    assert c.classify_sample({"sample_type": "Unknown"}) == "UNCLASSIFIED"


def test_query_cases_posts(monkeypatch):
    seen = {}
    def fake(endpoint, payload, timeout=30):
        seen["endpoint"] = endpoint
        seen["payload"] = payload
        return {"data": {"hits": [{"case_id": "c1", "samples": []}]}}
    monkeypatch.setattr(c, "_post_json", fake)
    rows = c.query_cases("TCGA-STAD")
    assert rows[0]["case_id"] == "c1"
    assert seen["endpoint"] == "cases"
    assert seen["payload"]["filters"]["content"]["value"] == ["TCGA-STAD"]


def test_query_variant_files_filters_variants(monkeypatch):
    def fake(endpoint, payload, timeout=30):
        return {"data": {"hits": [
            {"file_id": "v", "data_category": "Simple Nucleotide Variation"},
            {"file_id": "x", "data_category": "Transcriptome Profiling"},
        ]}}
    monkeypatch.setattr(c, "_post_json", fake)
    rows = c.query_variant_files("TCGA-STAD")
    assert [r["file_id"] for r in rows] == ["v"]


def test_build_cohort_manifest():
    cases = [{
        "case_id": "c1", "submitter_id": "TCGA-XX",
        "samples": [
            {"sample_id": "s1", "submitter_id": "S1", "sample_type": "Primary Tumor"},
            {"sample_id": "s2", "submitter_id": "S2", "sample_type": "Solid Tissue Normal"},
            {"sample_id": "s3", "submitter_id": "S3", "sample_type": "Other"},
        ],
    }]
    m = c.build_cohort_manifest("TCGA-STAD", cases, [{"file_id": "v"}])
    assert m["sample_count"] == 3
    assert m["tumor_sample_count"] == 1
    assert m["normal_sample_count"] == 1
    assert m["excluded_sample_count"] == 1
    assert m["analysis_ready"] is False


def test_write_manifest(tmp_path):
    m = c.build_cohort_manifest("TCGA-STAD", [])
    p = c.write_cohort_manifest(tmp_path / "cohort.json", m)
    assert json.loads(p.read_text())["schema_version"] == "A12-1"


def test_query_cases_paginates(monkeypatch):
    calls = []
    def fake(endpoint, payload, timeout=30):
        calls.append(payload["from"])
        if len(calls) == 1:
            return {"data": {"hits": [{"case_id": "c1"}], "pagination": {"total": 2}}}
        return {"data": {"hits": [{"case_id": "c2"}], "pagination": {"total": 2}}}
    monkeypatch.setattr(c, "_post_json", fake)
    rows = c.query_cases("TCGA-STAD", size=1)
    assert [x["case_id"] for x in rows] == ["c1", "c2"]
    assert calls == [0, 1]


def test_query_variant_files_paginates(monkeypatch):
    calls = []
    def fake(endpoint, payload, timeout=30):
        calls.append(payload["from"])
        if len(calls) == 1:
            return {"data": {"hits": [{"file_id": "v1", "data_category": "Simple Nucleotide Variation"}], "pagination": {"total": 2}}}
        return {"data": {"hits": [{"file_id": "v2", "data_category": "Simple Nucleotide Variation"}], "pagination": {"total": 2}}}
    monkeypatch.setattr(c, "_post_json", fake)
    rows = c.query_variant_files("TCGA-STAD", size=1)
    assert [x["file_id"] for x in rows] == ["v1", "v2"]
    assert calls == [0, 1]
