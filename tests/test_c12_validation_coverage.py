from wgr_cdp.research.validation_coverage import compare_frozen_panel_coverage


def test_frozen_panel_is_not_reoptimized():
    discovery = {
        "D1": {"A": 1, "B": 0},
        "D2": {"A": 0, "B": 1},
    }
    validation = {
        "V1": {"A": 1, "B": 0},
        "V2": {"A": 0, "B": 0},
        "V3": {"A": 0, "B": 1},
    }
    out = compare_frozen_panel_coverage(discovery, validation, ["A", "B"])
    assert out["status"] == "Available"
    assert out["reoptimized"] is False
    assert out["validation_coverage"] == 2 / 3


def test_validation_coverage_preserves_unavailable():
    out = compare_frozen_panel_coverage({"D1": {"A": 1}}, {}, ["A"])
    assert out["status"] == "Data unavailable"
