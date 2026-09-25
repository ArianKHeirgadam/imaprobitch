from wgr_cdp.discovery.candidate import generate_candidates
from wgr_cdp.discovery.scoring import score_candidate
from wgr_cdp.discovery.ranking import rank_candidates


def test_candidate_generation():
    candidates = generate_candidates({"vaf": 0.4})
    assert len(candidates) == 1
    assert candidates[0]["feature"] == "vaf"


def test_candidate_scoring_and_ranking():
    candidates = [
        {"feature": "a", "score": 1},
        {"feature": "b", "score": 5},
    ]

    ranked = rank_candidates(candidates)

    assert ranked[0]["feature"] == "b"
    assert score_candidate({"feature": "a"}, {"a": 2}) == 2
