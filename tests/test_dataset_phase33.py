from wgr_cdp.dataset import DatasetManifest, validate_dataset

def test_dataset_manifest(tmp_path):
    yaml_file = tmp_path / "dataset.yaml"

    yaml_file.write_text(
        '''
project:
  name: Test

reference:
  genome: GRCh38

samples:
  - id: C1
    group: cancer
  - id: H1
    group: healthy
''',
        encoding="utf-8"
    )

    dataset = DatasetManifest(yaml_file)

    assert dataset.count() == 2
    assert "cancer" in dataset.groups()
    assert "healthy" in dataset.groups()

def test_dataset_validation(tmp_path):
    yaml_file = tmp_path / "dataset.yaml"

    yaml_file.write_text(
        '''
samples:
 - id: C1
   group: cancer
 - id: H1
   group: healthy
''',
        encoding="utf-8"
    )

    dataset = DatasetManifest(yaml_file)
    result = validate_dataset(dataset)

    assert result["valid"] is True
