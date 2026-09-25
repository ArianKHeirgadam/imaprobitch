"""Candidate evaluation metrics."""


def confidence_score(observations, support):
    if observations <= 0:
        return 0

    return support / observations
