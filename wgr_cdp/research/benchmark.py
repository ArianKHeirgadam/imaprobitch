"""Exact-vs-WGR-CDP benchmarking with runtime and peak-memory measurements."""
from __future__ import annotations

import time
import tracemalloc
from collections import defaultdict


def _run(fn, data):
    tracemalloc.start()
    started = time.perf_counter()
    output = fn(data)
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return output, elapsed, peak


def _hit_key(row):
    return (str(row.get("region")), str(row.get("feature_type")))


def _hits_exact(output):
    rows = output if isinstance(output, list) else output.get("final", [])
    return {_hit_key(row) for row in rows if row.get("significant")}


def _hits_fast(output):
    return {_hit_key(row) for row in output.get("final", []) if row.get("significant")}


def _classification(exact_hits, fast_hits):
    tp = len(exact_hits & fast_hits)
    fp = len(fast_hits - exact_hits)
    fn = len(exact_hits - fast_hits)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "recall": tp / len(exact_hits) if exact_hits else 1.0,
        "precision": tp / len(fast_hits) if fast_hits else (1.0 if not exact_hits else 0.0),
    }


def benchmark(exact_fn, fast_fn, data):
    """Run one fair exact-vs-WGR-CDP comparison."""
    exact, exact_runtime, exact_peak = _run(exact_fn, data)
    fast, fast_runtime, fast_peak = _run(fast_fn, data)
    exact_hits = _hits_exact(exact)
    fast_hits = _hits_fast(fast)
    metrics = _classification(exact_hits, fast_hits)
    return {
        **metrics,
        "exact_runtime_s": exact_runtime,
        "fast_runtime_s": fast_runtime,
        "exact_peak_bytes": exact_peak,
        "fast_peak_bytes": fast_peak,
        "exact_hits": len(exact_hits),
        "fast_hits": len(fast_hits),
        "regions_evaluated_exact": len(exact) if isinstance(exact, list) else 0,
        "regions_evaluated_fast": len(fast.get("retained_regions", [])),
        "runtime_ratio_fast_over_exact": fast_runtime / exact_runtime if exact_runtime else None,
        "peak_memory_ratio_fast_over_exact": fast_peak / exact_peak if exact_peak else None,
    }


def _filter_rows(rows, feature_type=None):
    if feature_type is None:
        return list(rows)
    return [row for row in rows if str(row.get("feature_type", "SNV")).upper() == feature_type]


def benchmark_by_feature(exact_fn, fast_fn, data):
    """Return the same benchmark metrics independently for each feature type."""
    features = sorted({str(r.get("feature_type", "SNV")).upper() for r in data})
    return {feature: benchmark(exact_fn, fast_fn, _filter_rows(data, feature)) for feature in features}


def parameter_sweep(exact_fn, fast_fn_factory, data, parameters):
    """Evaluate explicit WGR-CDP settings as a recall-vs-cost table."""
    rows = []
    for parameter in parameters:
        result = benchmark(exact_fn, fast_fn_factory(parameter), data)
        rows.append({"parameter": parameter, **result})
    rows.sort(key=lambda row: (row["fast_runtime_s"], str(row["parameter"])))
    for rank, row in enumerate(rows, 1):
        row["cost_rank"] = rank
    return rows


def recall_vs_cost(results):
    """Return the non-dominated recall/cost frontier without hiding measurements."""
    ordered = sorted(results, key=lambda r: (r["fast_runtime_s"], r.get("fast_peak_bytes", 0)))
    frontier = []
    best_recall = -1.0
    for row in ordered:
        if row["recall"] >= best_recall:
            frontier.append(dict(row))
            best_recall = row["recall"]
    return frontier


def benchmark_summary(exact_fn, fast_fn, data):
    """Return primary metrics plus feature and coarse-resolution breakdowns."""
    primary = benchmark(exact_fn, fast_fn, data)
    by_feature = benchmark_by_feature(exact_fn, fast_fn, data)
    fast_output = fast_fn(data)
    resolution_counts = defaultdict(int)
    for row in fast_output.get("lineage", []):
        resolution_counts[str(row.get("resolution"))] += 1
    return {
        "primary": primary,
        "by_feature_type": by_feature,
        "fast_resolution_evaluated": dict(sorted(resolution_counts.items())),
    }
