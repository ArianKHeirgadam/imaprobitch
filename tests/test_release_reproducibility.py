import json
from pathlib import Path

from wgr_cdp.release.reproducibility import (
    sha256_file,
    collect_artifact_manifest,
    build_reproducibility_manifest,
    write_reproducibility_manifest,
    release_readiness,
)


def test_sha256_is_stable(tmp_path):
    p = tmp_path / "x.txt"
    p.write_text("abc", encoding="utf-8")
    assert len(sha256_file(p)) == 64
    assert sha256_file(p) == sha256_file(p)


def test_artifact_manifest_hashes_files(tmp_path):
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")
    result = collect_artifact_manifest(tmp_path)
    assert result["status"] == "Available"
    assert result["artifact_count"] == 1
    assert result["artifacts"][0]["path"] == "a.json"


def test_missing_output_is_data_unavailable(tmp_path):
    result = collect_artifact_manifest(tmp_path / "missing")
    assert result["status"] == "Data unavailable"


def test_reproducibility_manifest_contains_scope_and_artifacts(tmp_path):
    (tmp_path / "result.json").write_text('{"ok": true}', encoding="utf-8")
    result = build_reproducibility_manifest(
        tmp_path,
        config={"alpha": 0.05},
        run_id="run-001",
    )
    assert result["schema_version"] == "A9-1"
    assert result["run_id"] == "run-001"
    assert result["clinical_diagnostic"] is False
    assert result["artifacts"]["artifact_count"] == 1
    assert result["artifacts"]["artifacts"][0]["sha256"]


def test_manifest_writer_is_machine_readable(tmp_path):
    path = write_reproducibility_manifest(tmp_path, config={"depth": 300}, run_id="r1")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "r1"
    assert Path(path).exists()


def test_release_readiness_is_not_biological_validation():
    result = release_readiness()
    assert result["status"] == "PASS"
    assert result["scientific_results"] == "CONDITIONAL"
