import hashlib
import json

from wgr_cdp.data_ingestion import gdc_acquisition as a


def test_classify_modalities():
    assert a.classify_file({"data_format": "VCF", "data_category": "Simple Nucleotide Variation"}) == "SNV_INDEL"
    assert a.classify_file({"data_category": "Copy Number Variation", "data_type": "Copy Number Segment"}) == "CNV"
    assert a.classify_file({"data_category": "DNA Methylation"}) == "METHYLATION"


def test_build_manifest_selects_and_sorts():
    files = [
        {"file_id": "b", "data_category": "Copy Number Variation"},
        {"file_id": "a", "data_format": "VCF", "data_category": "Simple Nucleotide Variation"},
    ]
    m = a.build_acquisition_manifest("TCGA-STAD", files, {"SNV_INDEL"})
    assert m["selected_count"] == 1
    assert m["files"][0]["file_id"] == "a"
    assert m["files"][0]["download_status"] == "planned"


def test_verify_file(tmp_path):
    p = tmp_path / "x.txt"
    p.write_bytes(b"abc")
    md5 = hashlib.md5(b"abc").hexdigest()
    r = a.verify_file(p, md5, 3)
    assert r["verified"] is True
    assert r["status"] == "PASS"


def test_verify_bad_checksum(tmp_path):
    p = tmp_path / "x.txt"
    p.write_bytes(b"abc")
    r = a.verify_file(p, "bad", 3)
    assert r["verified"] is False
    assert r["status"] == "FAIL"


def test_download_controlled_requires_token(tmp_path):
    r = a.download_file({"file_id": "x", "access": "controlled"}, tmp_path)
    assert r["status"] == "Data unavailable"
    assert r["reason"] == "gdc_token_required"


def test_download_file_uses_endpoint(monkeypatch, tmp_path):
    class FakeResponse:
        def __init__(self):
            self._sent = False
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, n=-1):
            if self._sent:
                return b""
            self._sent = True
            return b"abc"
    seen = {}
    def fake_open(request, timeout=60):
        seen["url"] = request.full_url
        return FakeResponse()
    monkeypatch.setattr(a, "urlopen", fake_open)
    import hashlib
    row = {"file_id": "uuid", "file_name": "x.txt", "access": "open",
           "md5sum": hashlib.md5(b"abc").hexdigest(), "file_size": 3}
    r = a.download_file(row, tmp_path)
    assert r["verified"] is True
    assert "api.gdc.cancer.gov/data/uuid" in seen["url"]


def test_register_dataset(tmp_path):
    m = {"project_id": "TCGA-STAD", "files": [{
        "file_id": "x", "file_name": "x.vcf.gz", "local_path": str(tmp_path / "x.vcf.gz"),
        "md5sum": "abc", "file_size": 1, "modality": "SNV_INDEL",
        "access": "open", "verified": True
    }]}
    r = a.register_dataset(m, tmp_path)
    assert r["registered_count"] == 1
    assert r["analysis_ready_count"] == 0
    assert r["files"][0]["genome_build"] == "Data unavailable"


def test_write_manifests(tmp_path):
    m = a.build_acquisition_manifest("TCGA-STAD", [{"file_id":"x"}])
    jp = a.write_acquisition_manifest(tmp_path/"a.json", m)
    tp = a.write_tsv_manifest(tmp_path/"a.tsv", m)
    assert json.loads(jp.read_text())["project_id"] == "TCGA-STAD"
    assert "file_id" in tp.read_text()


def test_inventory_paginates(monkeypatch):
    calls = []
    def fake(url, timeout=30):
        calls.append(url)
        if len(calls) == 1:
            return {"data": {"hits": [{"file_id": "b"}], "pagination": {"total": 2}}}
        return {"data": {"hits": [{"file_id": "a"}], "pagination": {"total": 2}}}
    monkeypatch.setattr(a, "_get_json", fake)
    rows = a.inventory_files("TCGA-STAD", page_size=1)
    assert [r["file_id"] for r in rows] == ["b", "a"]
    assert len(calls) == 2


def test_acquire_manifest_keeps_unavailable_without_fake_success(tmp_path):
    m = a.build_acquisition_manifest("TCGA-STAD", [{"file_id": "x", "access": "controlled"}])
    result = a.acquire_manifest(m, tmp_path)
    assert result["verified_count"] == 0
    assert result["acquisition_status"] == "Data unavailable"
    assert result["files"][0]["verified"] is False


def test_download_file_curl_fallback_and_size_reporting(monkeypatch, tmp_path):
    calls = {"curl": 0}

    def failing_open(*args, **kwargs):
        raise OSError("simulated TLS EOF")

    class Completed:
        returncode = 0

    def fake_run(command, check=False):
        calls["curl"] += 1
        output = command[command.index("--output") + 1]
        import pathlib
        pathlib.Path(output).write_bytes(b"abc")
        return Completed()

    monkeypatch.setattr(a, "urlopen", failing_open)
    monkeypatch.setattr(a.shutil, "which", lambda name: "curl.exe")
    monkeypatch.setattr(a.subprocess, "run", fake_run)

    row = {
        "file_id": "uuid",
        "file_name": "x.txt",
        "access": "open",
        "md5sum": hashlib.md5(b"abc").hexdigest(),
        "file_size": 3,
    }
    manifest = a.build_acquisition_manifest("TCGA-STAD", [row])
    result = a.acquire_manifest(manifest, tmp_path)

    assert calls["curl"] == 1
    assert result["acquisition_status"] == "PASS"
    assert result["verified_count"] == 1
    assert result["selected_size_bytes"] == 3
    assert result["selected_size_mb"] == round(3 / 1024**2, 2)
    assert result["selected_size_gb"] == round(3 / 1024**3, 3)
    assert result["downloaded_size_bytes"] == 3
