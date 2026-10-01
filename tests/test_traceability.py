import pytest

from wgr_cdp.traceability import (
    assert_trace_membership,
    build_trace_record,
    validate_trace_record,
)


def test_build_trace_record():
    trace = build_trace_record(
        "run-001",
        ["in-1", "in-2"],
        ["out-1"],
    )
    assert trace == {
        "run_id": "run-001",
        "input_artifact_ids": ["in-1", "in-2"],
        "output_artifact_ids": ["out-1"],
    }


def test_missing_trace_field_rejected():
    with pytest.raises(ValueError):
        validate_trace_record({"run_id": "run-001"})


def test_blank_run_id_rejected():
    with pytest.raises(ValueError):
        build_trace_record("", [], [])


@pytest.mark.parametrize("field", ["input_artifact_ids", "output_artifact_ids"])
def test_artifact_ids_must_be_sequences(field):
    payload = {
        "run_id": "run-001",
        "input_artifact_ids": [],
        "output_artifact_ids": [],
    }
    payload[field] = "artifact-1"
    with pytest.raises(ValueError):
        validate_trace_record(payload)


def test_blank_artifact_id_rejected():
    with pytest.raises(ValueError):
        build_trace_record("run-001", ["in-1", ""], [])


def test_duplicate_artifact_ids_rejected():
    with pytest.raises(ValueError):
        build_trace_record("run-001", ["in-1", "in-1"], [])


def test_membership_checks():
    trace = build_trace_record("run-001", ["in-1"], ["out-1"])
    assert assert_trace_membership(trace, input_artifact_id="in-1")
    assert assert_trace_membership(trace, output_artifact_id="out-1")
    assert not assert_trace_membership(trace, input_artifact_id="in-9")
    assert not assert_trace_membership(trace, output_artifact_id="out-9")


def test_membership_with_no_specific_artifact_is_valid():
    trace = build_trace_record("run-001", [], [])
    assert assert_trace_membership(trace)
