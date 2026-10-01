import pytest

from wgr_cdp.status_validation import (
    validate_feature_record,
    validate_feature_records,
    set_feature_status,
    set_workflow_status,
)
from wgr_cdp.status import (
    DATA_UNAVAILABLE,
    DETECTED,
    NOT_DETECTED,
    PASS,
)


def test_missing_feature_status_defaults_to_data_unavailable():
    result = validate_feature_record({"region": "1:100"})
    assert result["status"] == DATA_UNAVAILABLE


def test_feature_record_preserves_other_fields():
    result = validate_feature_record(
        {"region": "1:100", "value": 0.25, "status": DETECTED}
    )
    assert result == {
        "region": "1:100",
        "value": 0.25,
        "status": DETECTED,
    }


def test_feature_records_are_validated():
    result = validate_feature_records(
        [
            {"status": DETECTED},
            {"status": NOT_DETECTED},
            {},
        ]
    )
    assert [row["status"] for row in result] == [
        DETECTED,
        NOT_DETECTED,
        DATA_UNAVAILABLE,
    ]


def test_invalid_feature_record_status_is_rejected():
    with pytest.raises(ValueError):
        validate_feature_record({"status": "unavailable"})


def test_set_feature_status_accepts_only_feature_statuses():
    record = {}
    set_feature_status(record, NOT_DETECTED)
    assert record["status"] == NOT_DETECTED

    with pytest.raises(ValueError):
        set_feature_status(record, PASS)


def test_set_workflow_status_accepts_workflow_statuses():
    record = {}
    set_workflow_status(record, PASS)
    assert record["status"] == PASS

    with pytest.raises(ValueError):
        set_workflow_status(record, DETECTED)
