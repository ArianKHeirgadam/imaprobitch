"""Candidate generation framework."""


def generate_candidates(features):
    """
    Generate discovery candidates from a feature dictionary.
    This is a framework layer; no biological claims are made.
    """
    if not isinstance(features, dict):
        return []

    return [
        {
            "feature": key,
            "value": value,
        }
        for key, value in features.items()
    ]
