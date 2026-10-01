import pytest

from wgr_cdp.exact_scanner_contract import (
    ExactScanRequest,
    ExactScanResult,
    unavailable_exact_scan_result,
    validate_exact_scan_result,
)
from wgr_cdp.status import DATA_UNAVAILABLE, DETECTED


def test_request_round_trip():
    request = ExactScanRequest(
        feature_type="SNV",
        resolution="base",
        records=({"patient": "P1", "value": 1},),
    )
    assert request.to_dict()["feature_type"] == "SNV"


def test_request_requires_records():
    with pytest.raises(ValueError):
        ExactScanRequest("SNV", "base", ())


def test_request_alpha_is_bounded():
    with pytest.raises(ValueError):
        ExactScanRequest("SNV", "base", ({"value": 1},), alpha=1.0)


def test_result_round_trip():
    result = ExactScanResult(
        "SNV",
        "base",
        DETECTED,
        ({"region": "chr1:100", "p_value": 0.01},),
        1,
    )
    assert result.to_dict()["records_evaluated"] == 1


def test_result_rejects_negative_count():
    with pytest.raises(ValueError):
        ExactScanResult("SNV", "base", DETECTED, (), -1)


def test_result_validation():
    payload = {
        "feature_type": "CNV",
        "resolution": 1000,
        "status": DETECTED,
        "candidates": [],
        "records_evaluated": 5,
    }
    assert validate_exact_scan_result(payload) == payload


def test_result_requires_all_fields():
    with pytest.raises(ValueError):
        validate_exact_scan_result(
            {
                "feature_type": "SNV",
                "resolution": "base",
                "status": DETECTED,
            }
        )


def test_result_candidates_must_be_sequence():
    payload = {
        "feature_type": "SNV",
        "resolution": "base",
        "status": DETECTED,
        "candidates": {},
        "records_evaluated": 1,
    }
    with pytest.raises(ValueError):
        validate_exact_scan_result(payload)


def test_unavailable_scan_is_explicit():
    result = unavailable_exact_scan_result(
        "METHYLATION",
        1000,
        reason="input assay unavailable",
    )
    assert result.status == DATA_UNAVAILABLE
    assert result.candidates[0]["status"] == DATA_UNAVAILABLE
