def test_phase31_import():
    from wgr_cdp.application.workflow import run_research_workflow
    assert callable(run_research_workflow)
