from wgr_cdp.research.panel_optimizer import panel_coverage, alpha_budget


def test_missing_panel_observation_is_not_negative():
    matrix = {"P1": {"A": 1.0}, "P2": {"B": 1.0}}
    assert panel_coverage(matrix, ["A"]) == 1.0


def test_explicit_zero_remains_observed_non_detection():
    matrix = {"P1": {"A": 0.0}, "P2": {}}
    assert panel_coverage(matrix, ["A"]) == 0.0


def test_panel_fpr_budget_validates_and_caps_k():
    assert 0 < alpha_budget(0.05, 50) <= 0.05
    import pytest
    with pytest.raises(ValueError):
        alpha_budget(float("nan"), 2)
