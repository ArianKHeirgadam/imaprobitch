"""Candidate scoring framework."""


def score_candidate(candidate, weights=None):
    if weights is None:
        weights = {}

    feature = candidate.get("feature")

    return weights.get(feature, 0)
