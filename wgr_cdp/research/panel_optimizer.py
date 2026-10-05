"""Complementary patient-coverage panel optimization."""
from itertools import combinations
import math
from .statistics import per_feature_alpha

def panel_coverage(matrix, selected):
    """Coverage over patients with at least one observed selected feature.

    Missing candidate observations are excluded from the denominator rather than
    being interpreted as explicit non-detection. Explicit numeric zero remains
    a valid observed non-detection.
    """
    if not matrix or not selected:
        return 0.0
    total = 0.0
    observed_patients = 0
    for row in matrix.values():
        observed = []
        for candidate in selected:
            if candidate not in row or row.get(candidate) is None:
                continue
            try:
                value = float(row[candidate])
            except (TypeError, ValueError, OverflowError):
                continue
            if not math.isfinite(value):
                continue
            observed.append(max(0.0, min(1.0, value)))
        if not observed:
            continue
        miss = 1.0
        for value in observed:
            miss *= 1.0 - value
        total += 1.0 - miss
        observed_patients += 1
    return total / observed_patients if observed_patients else 0.0

def greedy_panel(matrix,max_k=15,min_gain=.02):
    max_k = min(15, max(0, int(max_k)))
    min_gain = max(0.0, float(min_gain))
    candidates=sorted({c for row in matrix.values() for c in row}); selected=[]; current=0
    while candidates and len(selected)<max_k:
        best=max(candidates,key=lambda c:(panel_coverage(matrix,selected+[c]),c))
        new=panel_coverage(matrix,selected+[best])
        if selected and new-current<min_gain: break
        selected.append(best); candidates.remove(best); current=new
    return {"method":"greedy","selected":selected,"coverage":current,"k":len(selected)}

def ilp_panel(matrix,max_k=15,min_gain=0,max_candidates=22):
    """Exact binary optimization fallback; external ILP solvers may replace this for large spaces."""
    max_k = min(15, max(0, int(max_k)))
    min_gain = max(0.0, float(min_gain))
    candidates=sorted({c for row in matrix.values() for c in row})
    if len(candidates)>max_candidates:
        return {"method":"exact_0_1","status":"not_run","reason":"too_many_candidates","selected":[],"coverage":0.0,"k":0}
    best=(0.0,())
    for k in range(1,min(max_k,len(candidates))+1):
        for combo in combinations(candidates,k):
            cov=panel_coverage(matrix,combo)
            if cov>best[0]+1e-12: best=(cov,combo)
    return {"method":"exact_0_1","status":"optimal","selected":list(best[1]),"coverage":best[0],"k":len(best[1])}

def alpha_budget(fpr_target,k):
    target = float(fpr_target)
    if not math.isfinite(target) or not 0.0 < target <= 1.0:
        raise ValueError("fpr_target must be a finite number in (0, 1]")
    k = min(15, max(1, int(k)))
    return per_feature_alpha(target, k)

def coverage_curve(matrix, max_k=15, min_gain=0.02):
    """Return coverage and marginal gain for each panel size."""
    if not matrix:
        return []
    max_k = min(15, max(0, int(max_k)))
    candidates = sorted({c for row in matrix.values() for c in row})
    selected = []
    previous = 0.0
    curve = []
    while candidates and len(selected) < max_k:
        best = max(candidates, key=lambda c: (panel_coverage(matrix, selected + [c]), c))
        coverage = panel_coverage(matrix, selected + [best])
        gain = coverage - previous
        if selected and gain < float(min_gain):
            break
        selected.append(best)
        candidates.remove(best)
        curve.append({"k": len(selected), "candidate": best, "coverage": coverage, "marginal_gain": gain})
        previous = coverage
    return curve


def greedy_vs_ilp(matrix, max_k=15, min_gain=0.02):
    """Compare deterministic greedy selection with exact 0/1 optimization when feasible."""
    if not matrix:
        return {"status": "Data unavailable"}
    greedy = greedy_panel(matrix, max_k=min(15, int(max_k)), min_gain=min_gain)
    exact = ilp_panel(matrix, max_k=min(15, int(max_k)), min_gain=min_gain)
    return {
        "status": "Available",
        "greedy": greedy,
        "ilp": exact,
        "coverage_delta_ilp_minus_greedy": (
            float(exact["coverage"]) - float(greedy["coverage"])
            if exact.get("status") == "optimal" else "Data unavailable"
        ),
    }


def panel_bootstrap_stability(matrix, max_k=15, n_bootstrap=200, seed=42):
    """Bootstrap patient rows and measure how often each candidate is selected."""
    if not matrix:
        return {"status": "Data unavailable", "n_bootstrap": 0, "selection_frequency": {}}
    from random import Random
    rows = list(matrix.items())
    if not rows:
        return {"status": "Data unavailable", "n_bootstrap": 0, "selection_frequency": {}}
    rng = Random(seed)
    counts = {}
    for _ in range(int(n_bootstrap)):
        sample_rows = [rows[rng.randrange(len(rows))] for _ in rows]
        sample = {f"boot_{i}": row for i, (_, row) in enumerate(sample_rows)}
        selected = greedy_panel(sample, max_k=min(15, int(max_k)), min_gain=0.02)["selected"]
        for candidate in selected:
            counts[candidate] = counts.get(candidate, 0) + 1
    total = int(n_bootstrap)
    return {
        "status": "Available",
        "n_bootstrap": total,
        "max_k": min(15, int(max_k)),
        "seed": int(seed),
        "selection_frequency": {k: v / total for k, v in sorted(counts.items())},
    }


def layer_contribution(matrix, selected, candidate_layers):
    """Measure marginal coverage contribution by feature layer/type."""
    if not matrix:
        return {"status": "Data unavailable"}
    baseline = panel_coverage(matrix, selected)
    grouped = {}
    for candidate in selected:
        layer = str(candidate_layers.get(candidate, "Data unavailable"))
        grouped.setdefault(layer, []).append(candidate)
    result = {}
    for layer, members in grouped.items():
        without = [c for c in selected if c not in members]
        result[layer] = {
            "selected_n": len(members),
            "coverage_with_layer": baseline,
            "coverage_without_layer": panel_coverage(matrix, without),
            "marginal_contribution": baseline - panel_coverage(matrix, without),
        }
    return {"status": "Available", "baseline_coverage": baseline, "layers": result}
