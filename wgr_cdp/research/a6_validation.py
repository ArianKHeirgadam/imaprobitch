"""Phase A6: baseline comparison, ablation, bootstrap stability and validation.

All comparisons consume the same candidate universe and explicit constraints.
Missing validation inputs remain Data unavailable; no biological result is invented.
"""
from __future__ import annotations
from collections import Counter
from random import Random
from time import perf_counter
import tracemalloc

from .evidence import rank_candidates
from .panel_optimizer import panel_coverage, greedy_panel
from .validation import cohort_holdout_guard

A6_ABLATIONS = (
    "full_wgr_cdp",
    "without_detectability",
    "without_complementary_optimization",
    "without_blood_background",
    "without_early_stage",
    "without_specificity",
    "single_layer",
    "exact_scan_only",
)

def _id(row):
    return str(row.get("candidate_id") or row.get("feature") or row.get("candidate") or "")

def conventional_feature_ranking(candidates, k=15):
    """Conventional baseline: rank by statistical effect/evidence only."""
    rows=[]
    for row in candidates:
        x=dict(row)
        q=row.get("q_value")
        try:
            q=float(q)
            strength=1.0-q
        except (TypeError,ValueError):
            strength=None
        if strength is None:
            try: strength=float(row.get("frequency_difference", row.get("effect_size", 0.0)))
            except (TypeError,ValueError): strength=0.0
        x["_baseline_strength"]=max(0.0,min(1.0,float(strength)))
        rows.append(x)
    rows.sort(key=lambda r:(-r["_baseline_strength"],_id(r)))
    return rows[:max(0,int(k))]

def _timed(fn,*args,**kwargs):
    tracemalloc.start()
    t0=perf_counter()
    value=fn(*args,**kwargs)
    runtime=perf_counter()-t0
    _,peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return value,runtime,peak

def overlap_metrics(reference, candidate):
    a={_id(x) for x in reference}; b={_id(x) for x in candidate}
    tp=len(a&b)
    return {
        "reference_n":len(a),"candidate_n":len(b),"overlap":tp,
        "recall":tp/len(a) if a else None,
        "precision":tp/len(b) if b else None,
    }

def _coverage(matrix, selected):
    if matrix is None:
        return "Data unavailable"
    return panel_coverage(matrix, selected)

def compare_baseline(candidates, wgr_ranked, matrix=None, k=15):
    """Run conventional baseline and WGR ranking on identical candidates."""
    baseline,runtime_base,memory_base=_timed(conventional_feature_ranking,candidates,k)
    wgr=wgr_ranked[:max(0,int(k))]
    _,runtime_wgr,memory_wgr=_timed(lambda: list(wgr))
    metrics=overlap_metrics(baseline,wgr)
    metrics["interpretation"]="selection_overlap_not_predictive_performance"
    return {
        "baseline":{"method":"conventional_feature_ranking","selected":[_id(x) for x in baseline],
                    "runtime_s":runtime_base,"peak_bytes":memory_base,
                    "coverage":_coverage(matrix,[_id(x) for x in baseline])},
        "wgr_cdp":{"method":"integrated_evidence_ranking","selected":[_id(x) for x in wgr],
                   "coverage":_coverage(matrix,[_id(x) for x in wgr]),"runtime_s":runtime_wgr,"peak_bytes":memory_wgr},
        "overlap":metrics,
        "status":"Available" if candidates else "Data unavailable",
    }

def _ablation_weights(base_weights, name):
    weights=dict(base_weights)
    remove={
        "without_detectability":"detectability",
        "without_blood_background":"blood_background_safety",
        "without_early_stage":"early_stage_score",
        "without_specificity":"specificity_score",
        "single_layer":None,
    }.get(name,"__none__")
    if remove:
        weights.pop(remove,None)
    elif name=="single_layer":
        weights={k:1.0 for k in ("statistical_strength",)}
    elif name=="without_complementary_optimization":
        weights=dict(weights)
    return weights


def _optimized_selection(ranked, matrix, k):
    ids=[_id(x) for x in ranked]
    if not matrix:
        return ids[:k], "Data unavailable"
    restricted={p:{c:row.get(c,0) for c in ids if c in row} for p,row in matrix.items()}
    if not any(restricted.values()):
        return ids[:k], "Data unavailable"
    panel=greedy_panel(restricted,max_k=k,min_gain=0)
    return panel["selected"], "Available"

def run_ablations(candidates, base_weights, constraints=None, matrix=None, k=15):
    constraints=dict(constraints or {})
    output=[]
    for name in A6_ABLATIONS:
        if name=="full_wgr_cdp":
            weights=dict(base_weights)
        elif name in {"exact_scan_only","without_complementary_optimization"}:
            weights=dict(base_weights)
        else:
            weights=_ablation_weights(base_weights,name)
        ranking=rank_candidates(candidates,weights,constraints)
        ranked_ids=[_id(x) for x in ranking["ranked"]]
        selection_method="ranked_top_k"
        if name=="full_wgr_cdp":
            selected,selection_method=_optimized_selection(ranking["ranked"],matrix,k)
        else:
            selected=ranked_ids[:k]
        output.append({
            "ablation":name,"selected":selected,"k":len(selected),
            "coverage":_coverage(matrix,selected),
            "selection_method":selection_method,
            "ineligible":len(ranking["ineligible"]),
            "unscored":len(ranking["unscored"]),
            "weights":weights,
        })
    return output

def bootstrap_rank_stability(candidates, weights, constraints=None, n_bootstrap=200, k=15, seed=42):
    if not candidates:
        return {"status":"Data unavailable","n_bootstrap":0,"selection_frequency":{}}
    rng=Random(seed); counts=Counter()
    n=len(candidates)
    for _ in range(int(n_bootstrap)):
        sample=[candidates[rng.randrange(n)] for _ in range(n)]
        ranked=rank_candidates(sample,weights,constraints)["ranked"][:k]
        for row in ranked:
            counts[_id(row)]+=1
    return {
        "status":"Available","n_bootstrap":int(n_bootstrap),"k":int(k),"seed":int(seed),
        "selection_frequency":{key:value/int(n_bootstrap) for key,value in sorted(counts.items())},
    }

def validate_holdout(discovery_candidates, validation_candidates):
    discovery_ids=[_id(x) for x in discovery_candidates]
    validation_ids=[_id(x) for x in validation_candidates]
    cohort_holdout_guard(discovery_ids,validation_ids)
    d=set(discovery_ids); v=set(validation_ids)
    return {"status":"Available","discovery_n":len(d),"validation_n":len(v),"overlap":0}

def validate_panel(matrix, selected, min_coverage=None):
    if matrix is None:
        return {"status":"Data unavailable","coverage":"Data unavailable","passes":None}
    coverage=panel_coverage(matrix,selected)
    return {"status":"Available","coverage":coverage,
            "passes":None if min_coverage is None else coverage>=float(min_coverage)}


def evaluate_selected_candidates(selected, validation_candidates):
    """Re-evaluate discovery-selected candidates against a separate candidate table."""
    if validation_candidates is None:
        return {"status":"Data unavailable","selected_n":len(selected)}
    validation_ids={_id(row) for row in validation_candidates}
    selected=set(selected)
    found=selected & validation_ids
    return {
        "status":"Available",
        "selected_n":len(selected),
        "revalidated_n":len(found),
        "revalidation_rate":len(found)/len(selected) if selected else None,
        "revalidated_candidates":sorted(found),
    }

def run_a6(candidates, weights, constraints=None, matrix=None, k=15,
           n_bootstrap=200, validation_candidates=None, seed=42, labels=None):
    """Complete A6 evaluation record."""
    constraints=dict(constraints or {})
    ranking=rank_candidates(candidates,weights,constraints)
    baseline=compare_baseline(candidates,ranking["ranked"],matrix,k)
    ablations=run_ablations(candidates,weights,constraints,matrix,k)
    stability=bootstrap_rank_stability(candidates,weights,constraints,n_bootstrap,k,seed)
    holdout=evaluate_selected_candidates([_id(x) for x in ranking["ranked"][:k]], validation_candidates)
    return {
        "status":"Available" if candidates else "Data unavailable",
        "k":int(k),"constraints":constraints,
        "baseline_comparison":baseline,
        "ablations":ablations,
        "bootstrap_stability":stability,
        "holdout_validation":holdout,
        "baseline_models": {
            "logistic": logistic_baseline(candidates, labels=labels, k=k),
            "elastic_net": elastic_net_coordinate_descent(candidates, labels=labels, k=k),
        },
        "selected":[_id(x) for x in ranking["ranked"][:k]],
    }


def _design_matrix(candidates, features=None):
    """Build a deterministic numeric matrix with training-only median imputation.

    Missing/non-finite feature values are not treated as observed zeros. Imputation
    statistics are derived only from the supplied training rows.
    """
    import math
    features = list(features or sorted({
        key for row in candidates for key, value in row.items()
        if key not in {"candidate_id", "candidate", "feature", "gene"}
        and isinstance(value, (int, float)) and not isinstance(value, bool)
    }))
    observed = {}
    for feature in features:
        values = []
        for row in candidates:
            value = row.get(feature)
            try:
                value = float(value)
            except (TypeError, ValueError, OverflowError):
                continue
            if math.isfinite(value):
                values.append(value)
        if values:
            values.sort()
            mid = len(values) // 2
            observed[feature] = values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2.0
    features = [feature for feature in features if feature in observed]
    X = []
    for row in candidates:
        values = []
        for feature in features:
            try:
                value = float(row.get(feature))
            except (TypeError, ValueError, OverflowError):
                value = observed[feature]
            if not math.isfinite(value):
                value = observed[feature]
            values.append(value)
        X.append(values)
    return X, features


def _validated_binary_labels(labels, n):
    if labels is None or len(labels) != n or n == 0:
        return None
    output = []
    for value in labels:
        if isinstance(value, bool):
            output.append(float(value))
            continue
        try:
            value = float(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if value not in (0.0, 1.0):
            return None
        output.append(value)
    if len(set(output)) < 2:
        return None
    return output


def logistic_baseline(candidates, labels=None, k=15, l2=1e-2, steps=500, learning_rate=0.05):
    """Dependency-light logistic baseline; returns Data unavailable without labels."""
    labels = _validated_binary_labels(labels, len(candidates))
    if labels is None or not candidates:
        return {"status": "Data unavailable", "selected": [], "features": []}
    try:
        l2 = float(l2)
        steps = int(steps)
        learning_rate = float(learning_rate)
    except (TypeError, ValueError, OverflowError):
        return {"status": "Data unavailable", "selected": [], "features": []}
    import math
    if not math.isfinite(l2) or l2 < 0 or steps <= 0 or not math.isfinite(learning_rate) or learning_rate <= 0:
        return {"status": "Data unavailable", "selected": [], "features": []}
    X, features = _design_matrix(candidates)
    if not X or not features:
        return {"status": "Data unavailable", "selected": [], "features": features}
    y = labels
    weights = [0.0] * len(features)
    bias = 0.0
    import math
    for _ in range(int(steps)):
        grad_w = [0.0] * len(features)
        grad_b = 0.0
        for row, target in zip(X, y):
            z = bias + sum(w * x for w, x in zip(weights, row))
            z = max(-30.0, min(30.0, z))
            p = 1.0 / (1.0 + math.exp(-z))
            error = p - target
            grad_b += error
            for j, x in enumerate(row):
                grad_w[j] += error * x
        n = float(len(X))
        bias -= learning_rate * grad_b / n
        for j in range(len(weights)):
            weights[j] -= learning_rate * (grad_w[j] / n + l2 * weights[j])
    ranked = sorted(
        enumerate(weights),
        key=lambda item: (-abs(item[1]), item[0]),
    )
    return {
        "status": "Available",
        "features": features,
        "coefficients": {features[i]: weights[i] for i, _ in ranked},
        "selected": features[:0] + [features[i] for i, _ in ranked[:max(0, int(k))]],
        "bias": bias,
    }


def elastic_net_coordinate_descent(candidates, labels=None, alpha=0.01, l1_ratio=0.5,
                                   k=15, steps=500, learning_rate=0.02):
    """Dependency-light elastic-net coefficient baseline."""
    labels = _validated_binary_labels(labels, len(candidates))
    if labels is None or not candidates:
        return {"status": "Data unavailable", "selected": [], "features": []}
    try:
        alpha = float(alpha)
        l1_ratio = float(l1_ratio)
        steps = int(steps)
        learning_rate = float(learning_rate)
    except (TypeError, ValueError, OverflowError):
        return {"status": "Data unavailable", "selected": [], "features": []}
    import math
    if (not math.isfinite(alpha) or alpha < 0 or not 0 <= l1_ratio <= 1 or
            steps <= 0 or not math.isfinite(learning_rate) or learning_rate <= 0):
        return {"status": "Data unavailable", "selected": [], "features": []}
    X, features = _design_matrix(candidates)
    if not X or not features:
        return {"status": "Data unavailable", "selected": [], "features": features}
    y = labels
    weights = [0.0] * len(features)
    import math
    l1 = float(alpha) * float(l1_ratio)
    l2 = float(alpha) * (1.0 - float(l1_ratio))
    for _ in range(int(steps)):
        for j in range(len(features)):
            grad = 0.0
            for row, target in zip(X, y):
                z = sum(w * x for w, x in zip(weights, row))
                z = max(-30.0, min(30.0, z))
                p = 1.0 / (1.0 + math.exp(-z))
                grad += (p - target) * row[j]
            grad /= float(len(X))
            old = weights[j]
            proposal = old - learning_rate * (grad + l2 * old)
            threshold = learning_rate * l1
            if proposal > threshold:
                weights[j] = proposal - threshold
            elif proposal < -threshold:
                weights[j] = proposal + threshold
            else:
                weights[j] = 0.0
    ranked = sorted(enumerate(weights), key=lambda item: (-abs(item[1]), item[0]))
    return {
        "status": "Available",
        "features": features,
        "coefficients": {features[i]: weights[i] for i, _ in ranked},
        "selected": [features[i] for i, _ in ranked[:max(0, int(k))]],
        "alpha": float(alpha),
        "l1_ratio": float(l1_ratio),
    }
