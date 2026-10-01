import pytest

from wgr_cdp.dataset_status import (
    DATASET_PARTIAL,
    DATASET_UNAVAILABLE,
    DATASET_USABLE,
    assert_not_biological_negative,
    classify_dataset_status,
    dataset_status_reason,
)


def _manifest(status="partial"):
    return {"dataset_id": "TCGA-STAD", "status": status}


def test_status_reason_is_explicit():
    assert "available" in dataset_status_reason(DATASET_USABLE)
    assert "part" in dataset_status_reason(DATASET_PARTIAL)
    assert "unavailable" in dataset_status_reason(DATASET_UNAVAILABLE)


def test_custom_reason_is_preserved():
    reason = "controlled-access files were not downloaded"
    assert dataset_status_reason(DATASET_PARTIAL, reason=reason) == reason


@pytest.mark.parametrize("status", ["bad", "", None])
def test_invalid_status_rejected(status):
    with pytest.raises(ValueError):
        dataset_status_reason(status)


def test_classification_requires_required_inputs_for_usable():
    assert classify_dataset_status(
        _manifest(DATASET_PARTIAL),
        required_inputs_available=True,
    ) == DATASET_USABLE


def test_classification_marks_partial_inputs():
    assert classify_dataset_status(
        _manifest(DATASET_USABLE),
        required_inputs_available=False,
        partial_inputs_available=True,
    ) == DATASET_PARTIAL


def test_classification_marks_missing_inputs_unavailable():
    assert classify_dataset_status(
        _manifest(DATASET_USABLE),
        required_inputs_available=False,
        partial_inputs_available=False,
    ) == DATASET_UNAVAILABLE


def test_invalid_declared_status_rejected():
    with pytest.raises(ValueError):
        classify_dataset_status(
            _manifest("not-a-status"),
            required_inputs_available=True,
        )


def test_unavailable_cannot_be_negative_biological_evidence():
    with pytest.raises(ValueError):
        assert_not_biological_negative(DATASET_UNAVAILABLE, "Not detected")


def test_partial_cannot_be_negative_biological_evidence():
    with pytest.raises(ValueError):
        assert_not_biological_negative(DATASET_PARTIAL, "negative")


def test_usable_can_have_a_negative_biological_result():
    assert_not_biological_negative(DATASET_USABLE, "Not detected")


def test_unavailable_can_have_non_negative_placeholder():
    assert_not_biological_negative(DATASET_UNAVAILABLE, "Data unavailable")
