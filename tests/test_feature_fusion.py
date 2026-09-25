from wgr_cdp.fusion.fusion_engine import build_feature_vector
from wgr_cdp.fusion.validators import validate_feature_vector


def test_feature_merge():
    vector = build_feature_vector(
        "sample_001",
        {"vaf": 0.5},
        {"impact": "HIGH"}
    )

    assert vector.features["vaf"] == 0.5
    assert vector.features["impact"] == "HIGH"


def test_feature_vector_validation():
    vector = build_feature_vector(
        "sample_001",
        {"cnv": 2}
    )

    assert validate_feature_vector(vector)
