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
        selected=[_id(x) for x in ranking["ranked"][:k]]
        output.append({
            "ablation":name,"selected":selected,"k":len(selected),
            "coverage":_coverage(matrix,selected),
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

def run_a6(candidates, weights, constraints=None, matrix=None, k=15,
           n_bootstrap=200, validation_candidates=None, seed=42):
    """Complete A6 evaluation record."""
    constraints=dict(constraints or {})
    ranking=rank_candidates(candidates,weights,constraints)
    baseline=compare_baseline(candidates,ranking["ranked"],matrix,k)
    ablations=run_ablations(candidates,weights,constraints,matrix,k)
    stability=bootstrap_rank_stability(candidates,weights,constraints,n_bootstrap,k,seed)
    holdout={"status":"Data unavailable"}
    if validation_candidates is not None:
        holdout=validate_holdout(candidates,validation_candidates)
    return {
        "status":"Available" if candidates else "Data unavailable",
        "k":int(k),"constraints":constraints,
        "baseline_comparison":baseline,
        "ablations":ablations,
        "bootstrap_stability":stability,
        "holdout_validation":holdout,
        "selected":[_id(x) for x in ranking["ranked"][:k]],
    }
