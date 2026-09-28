from wgr_cdp.candidate_discovery import discover_candidates, score_candidate


def test_candidate_combines_cohort_and_external_evidence():
    cohort = [{
        "feature": "v1",
        "case_carriers": 8,
        "control_carriers": 1,
        "case_n": 10,
        "control_n": 10,
        "case_frequency": 0.8,
        "control_frequency": 0.1,
        "frequency_difference": 0.7,
        "case_control_frequency_ratio": 8.0,
        "p_value": 0.01,
    }]

    candidates = discover_candidates(
        cohort,
        annotations={
            "v1": {
                "clinvar_id": "123",
                "clinvar_accession": "VCV000123",
                "dbsnp_ref_snp_id": "rs123",
            }
        },
        functional_evidence={
            "v1": {
                "gene": "TP53",
                "consequence": "missense_variant",
                "impact": "MODERATE",
            }
        },
    )

    result = candidates[0]

    assert result["feature"] == "v1"
    assert result["candidate_rank"] == 1
    assert result["evidence_flags"] == {
        "clinvar": True,
        "dbsnp": True,
        "functional": True,
    }
    assert result["annotation"]["clinvar_id"] == "123"
    assert result["functional_evidence"]["gene"] == "TP53"
    assert result["evidence_score"] == 100.0


def test_candidate_handles_missing_external_evidence():
    candidates = discover_candidates([{
        "feature": "v2",
        "frequency_difference": 0.0,
        "p_value": 1.0,
    }])

    result = candidates[0]

    assert result["evidence_flags"] == {
        "clinvar": False,
        "dbsnp": False,
        "functional": False,
    }
    assert result["evidence_score"] == 0.0


def test_candidate_ranking_is_deterministic():
    cohort = [
        {
            "feature": "v_low",
            "frequency_difference": 0.1,
            "p_value": 0.05,
        },
        {
            "feature": "v_high",
            "frequency_difference": 0.8,
            "p_value": 0.001,
        },
    ]

    candidates = discover_candidates(cohort)

    assert [item["feature"] for item in candidates] == ["v_high", "v_low"]
    assert candidates[0]["candidate_rank"] == 1
    assert candidates[1]["candidate_rank"] == 2


def test_score_is_bounded():
    result = {
        "frequency_difference": 1.0,
        "p_value": 0.0001,
        "annotation": {
            "clinvar_id": "1",
            "dbsnp_ref_snp_id": "rs1",
        },
        "functional_evidence": {
            "gene": "TP53",
            "consequence": "missense_variant",
        },
    }

    assert 0.0 <= score_candidate(result) <= 100.0
