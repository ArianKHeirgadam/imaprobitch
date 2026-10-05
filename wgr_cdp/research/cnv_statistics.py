"""C-12.3: explicit statistical methods for CNV event and dosage data."""
from __future__ import annotations

import math
from itertools import combinations
from random import Random


def mean(values):
    values = [float(v) for v in values]
    return sum(values) / len(values) if values else None


def mean_difference(case_values, control_values):
    a, b = mean(case_values), mean(control_values)
    return None if a is None or b is None else a - b


def standardized_mean_difference(case_values, control_values):
    a = [float(v) for v in case_values]
    b = [float(v) for v in control_values]
    if len(a) < 2 or len(b) < 2:
        return None
    ma, mb = mean(a), mean(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    pooled_den = (len(a) + len(b) - 2)
    if pooled_den <= 0:
        return None
    pooled = math.sqrt(((len(a) - 1) * va + (len(b) - 1) * vb) / pooled_den)
    return None if pooled == 0 else (ma - mb) / pooled


def permutation_mean_p_value(case_values, control_values, permutations=999, seed=42):
    """Two-sided permutation p-value for a continuous CNV dosage contrast."""
    case = [float(v) for v in case_values]
    control = [float(v) for v in control_values]
    if not case or not control:
        return None
    n_perm = int(permutations)
    if n_perm <= 0:
        return None
    observed = abs(mean(case) - mean(control))
    pooled = case + control
    n_case = len(case)
    rng = Random(int(seed))
    extreme = 0
    # Exact enumeration when the problem is small enough; otherwise use
    # reproducible Monte-Carlo permutations.
    all_pairs = list(combinations(range(len(pooled)), n_case))
    if len(all_pairs) <= n_perm:
        draws = all_pairs
    else:
        draws = []
        for _ in range(n_perm):
            indices = list(range(len(pooled)))
            rng.shuffle(indices)
            draws.append(tuple(sorted(indices[:n_case])))
    for indices in draws:
        selected = set(indices)
        a = [pooled[i] for i in range(len(pooled)) if i in selected]
        b = [pooled[i] for i in range(len(pooled)) if i not in selected]
        if abs(mean(a) - mean(b)) >= observed - 1e-15:
            extreme += 1
    return (extreme + 1) / (len(draws) + 1)


def describe_cnv_statistics(case_values, control_values, permutations=999, seed=42):
    """Return a formal dosage statistical record without changing event counts."""
    p = permutation_mean_p_value(case_values, control_values, permutations, seed)
    return {
        "statistical_test": "permutation_test_mean_difference",
        "p_value": p,
        "effect_size": standardized_mean_difference(case_values, control_values),
        "mean_difference": mean_difference(case_values, control_values),
        "case_n": len(case_values),
        "control_n": len(control_values),
        "permutations": int(permutations),
        "seed": int(seed),
    }
