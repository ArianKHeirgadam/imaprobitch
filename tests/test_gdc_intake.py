import json

from wgr_cdp.data_ingestion import gdc


def test_build_intake_preserves_unavailable_and_provenance():
    record = gdc.build_intake_record(
        {
            "project_id": "TCGA-STAD",
            "name": "Stomach Adenocarcinoma",
            "summary": {"case_count": 10, "file_count": 20},
            "released": True,
        },
        {"data": {"hits": [{"file_id": "f1", "access": "open"}]}},
    )
    assert record["schema_version"] == "A10-1"
    assert record["source"] == "GDC"
    assert record["project_id"] == "TCGA-STAD"
    assert record["summary"]["case_count"] == 10
    assert record["files"][0]["file_id"] == "f1"
    assert record["downloaded_locally"] is False
    assert record["clinical_or_biological_results"] == "Data unavailable"


def test_build_intake_does_not_invent_missing_fields():
    record = gdc.build_intake_record({"project_id": "TCGA-STAD"})
    assert record["project_name"] == "Data unavailable"
    assert record["summary"]["case_count"] == "Data unavailable"
    assert record["disease_type"] == "Data unavailable"


def test_fetch_project_uses_gdc_endpoint(monkeypatch):
    seen = {}
    def fake(url, timeout=20):
        seen["url"] = url
        return {"data": {"project_id": "TCGA-STAD", "name": "STAD"}}
    monkeypatch.setattr(gdc, "_get_json", fake)
    result = gdc.fetch_project("TCGA-STAD")
    assert result["project_id"] == "TCGA-STAD"
    assert "api.gdc.cancer.gov/projects/TCGA-STAD?" in seen["url"]


def test_query_files_builds_project_filter(monkeypatch):
    seen = {}
    def fake(url, timeout=20):
        seen["url"] = url
        return {"data": {"hits": []}}
    monkeypatch.setattr(gdc, "_get_json", fake)
    result = gdc.query_files("TCGA-STAD", access="open")
    assert result["data"]["hits"] == []
    assert "cases.project.project_id" in seen["url"]
    assert "TCGA-STAD" in seen["url"]


def test_write_intake_record(tmp_path):
    path = gdc.write_intake_record(tmp_path / "intake.json", {"status": "Available"})
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "Available"
