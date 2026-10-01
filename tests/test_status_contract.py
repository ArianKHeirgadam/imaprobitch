import pytest

from wgr_cdp.status import (
    CONDITIONAL,
    DATA_UNAVAILABLE,
    DETECTED,
    FAIL,
    FEATURE_STATUSES,
    NOT_DETECTED,
    PASS,
    QUARANTINED,
    WARN,
    WORKFLOW_STATUSES,
    feature_status_from_value,
    validate_feature_status,
    validate_workflow_status,
)


def test_feature_status_contract_is_exact():
    assert FEATURE_STATUSES == {
        "Detected",
        "Not detected",
        "Data unavailable",
    }


def test_workflow_status_contract_is_separate():
    assert WORKFLOW_STATUSES == {
        "PASS",
        "FAIL",
        "WARN",
        "CONDITIONAL",
        "QUARANTINED",
    }


@pytest.mark.parametrize(
    "status",
    [DETECTED, NOT_DETECTED, DATA_UNAVAILABLE],
)
def test_feature_status_validation(status):
    assert validate_feature_status(status) == status


@pytest.mark.parametrize(
    "status",
    ["detected", "Not Detected", "Unavailable", "", None],
)
def test_invalid_feature_status_rejected(status):
    with pytest.raises(ValueError):
        validate_feature_status(status)


@pytest.mark.parametrize(
    "status",
    [PASS, FAIL, WARN, CONDITIONAL, QUARANTINED],
)
def test_workflow_status_validation(status):
    assert validate_workflow_status(status) == status


def test_workflow_and_feature_statuses_do_not_overlap():
    assert FEATURE_STATUSES.isdisjoint(WORKFLOW_STATUSES)


def test_missing_value_is_not_negative_evidence():
    assert feature_status_from_value(None) == DATA_UNAVAILABLE


def test_present_value_is_detected_by_helper():
    assert feature_status_from_value(0) == DETECTED
