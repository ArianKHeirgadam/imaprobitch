from wgr_cdp.pipeline.runner import execute_pipeline


def test_pipeline_execution():
    results = execute_pipeline({"sample": "sample_001"})

    assert len(results) == 8
    assert results[0]["stage"] == "manifest"
    assert results[-1]["stage"] == "evaluation"
