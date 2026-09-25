"""Validation rules for unified feature vectors."""


def validate_feature_vector(vector):
    if not vector.sample_id:
        return False

    if not isinstance(vector.features, dict):
        return False

    return True
