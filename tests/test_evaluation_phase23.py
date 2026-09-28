import pytest

from wgr_cdp.evaluation.benchmark import benchmark_binary_predictions
from wgr_cdp.evaluation.multiple_testing import (
    add_fdr,
    benjamini_hochberg,
    filter_significant,
)


def test_benjamini_hochberg_preserves_input_order():
    result = benjamini_hochberg([0.01, 0.04, 0.02])

    assert result == pytest.approx([0.03, 0.04, 0.03])


def test_benjamini_hochberg_empty_and_invalid():
    assert benjamini_hochberg([]) == []

    with pytest.raises(ValueError):
        benjamini_hochberg([0.01, 1.1])


def test_add_fdr_and_filter_significant():
    rows = [
        {"feature": "a", "p_value": 0.001},
        {"feature": "b", "p_value": 0.2},
        {"feature": "c", "p_value": 0.01},
    ]

    corrected = add_fdr(rows)
    selected = filter_significant(corrected, alpha=0.05)

    assert all("q_value" in row for row in corrected)
    assert [row["feature"] for row in selected] == ["a", "c"]
    assert rows[0] == {"feature": "a", "p_value": 0.001}


def test_fdr_filter_validates_alpha():
    with pytest.raises(ValueError):
        filter_significant([], alpha=0)


def test_binary_benchmark_summary():
    result = benchmark_binary_predictions(
        [1, 1, 0, 0],
        [1, 0, 1, 0],
    )

    assert result["tp"] == 1
    assert result["tn"] == 1
    assert result["fp"] == 1
    assert result["fn"] == 1
    assert result["accuracy"] == 0.5
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["specificity"] == 0.5
