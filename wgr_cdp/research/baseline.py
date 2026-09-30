"""Fair baseline API used by Phase A6.

The baseline ranks the exact same candidate universe as WGR-CDP and does not
claim clinical predictive performance.
"""
from .a6_validation import conventional_feature_ranking, logistic_score, elastic_net_coordinate_descent
def top_k(features,k=15):
    return conventional_feature_ranking(features,k)
