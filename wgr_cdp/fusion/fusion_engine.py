"""Feature fusion engine."""


def merge_features(*feature_sources):
    merged = {}

    for source in feature_sources:
        if source:
            merged.update(source)

    return merged


def build_feature_vector(sample_id, *feature_sources):
    from .feature_schema import UnifiedFeatureVector

    vector = UnifiedFeatureVector(sample_id=sample_id)
    vector.features = merge_features(*feature_sources)

    return vector
