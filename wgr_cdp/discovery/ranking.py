"""Candidate ranking framework."""


def rank_candidates(candidates):
    return sorted(
        candidates,
        key=lambda x: x.get("score", 0),
        reverse=True,
    )
