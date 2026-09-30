"""Sensitivity analysis for transparent candidate-weight configurations."""
from __future__ import annotations
from .evidence import rank_candidates
def normalize_weights(weights):
    weights={str(k):max(0.0,float(v)) for k,v in dict(weights).items()}; total=sum(weights.values())
    if total<=0: raise ValueError("at least one weight must be positive")
    return {k:v/total for k,v in weights.items()}
def weight_sensitivity(candidates,base_weights,scenarios,constraints=None):
    results=[]
    for name,overrides in scenarios:
        weights=dict(base_weights); weights.update(overrides); weights=normalize_weights(weights); ranking=rank_candidates(candidates,weights,constraints)
        results.append({"scenario":str(name),"weights":weights,"ranked_candidates":[r.get("candidate_id",r.get("candidate")) for r in ranking["ranked"]],"top_candidate":(ranking["ranked"][0].get("candidate_id",ranking["ranked"][0].get("candidate")) if ranking["ranked"] else None)})
    return results
def selection_stability(results):
    valid=[r for r in results if r.get("top_candidate") is not None]; counts={}
    for row in valid: counts[row["top_candidate"]]=counts.get(row["top_candidate"],0)+1
    total=len(valid)
    return {"n_scenarios":len(results),"n_valid_scenarios":total,"top_candidate_frequency":{k:v/total for k,v in counts.items()} if total else {},"status":"Available" if total else "Data unavailable"}
