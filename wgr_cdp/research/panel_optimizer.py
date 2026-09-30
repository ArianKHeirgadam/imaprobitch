"""Complementary patient-coverage panel optimization."""
from itertools import combinations
from .statistics import per_feature_alpha

def panel_coverage(matrix,selected):
    if not matrix: return 0.0
    total=0.0
    for row in matrix.values():
        miss=1.0
        for c in selected: miss*=1-max(0,min(1,float(row.get(c,0))))
        total+=1-miss
    return total/len(matrix)

def greedy_panel(matrix,max_k=15,min_gain=.02):
    candidates=sorted({c for row in matrix.values() for c in row}); selected=[]; current=0
    while candidates and len(selected)<max_k:
        best=max(candidates,key=lambda c:(panel_coverage(matrix,selected+[c]),c))
        new=panel_coverage(matrix,selected+[best])
        if selected and new-current<min_gain: break
        selected.append(best); candidates.remove(best); current=new
    return {"method":"greedy","selected":selected,"coverage":current,"k":len(selected)}

def ilp_panel(matrix,max_k=15,min_gain=0,max_candidates=22):
    """Exact binary optimization fallback; external ILP solvers may replace this for large spaces."""
    candidates=sorted({c for row in matrix.values() for c in row})
    if len(candidates)>max_candidates:
        return {"method":"exact_0_1","status":"not_run","reason":"too_many_candidates","selected":[],"coverage":0.0,"k":0}
    best=(0.0,())
    for k in range(1,min(max_k,len(candidates))+1):
        for combo in combinations(candidates,k):
            cov=panel_coverage(matrix,combo)
            if cov>best[0]+1e-12: best=(cov,combo)
    return {"method":"exact_0_1","status":"optimal","selected":list(best[1]),"coverage":best[0],"k":len(best[1])}

def alpha_budget(fpr_target,k): return per_feature_alpha(fpr_target,k)