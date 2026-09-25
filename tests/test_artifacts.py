from wgr_cdp.artifacts.manager import save_artifact, load_artifact
from wgr_cdp.artifacts.metadata import create_metadata


def test_artifact_save_load(tmp_path):
    file_path = tmp_path / "artifact.json"

    save_artifact({"score": 1}, file_path)

    result = load_artifact(file_path)

    assert result["score"] == 1


def test_metadata_creation():
    metadata = create_metadata("pipeline_result", "1.0")

    assert metadata["name"] == "pipeline_result"
