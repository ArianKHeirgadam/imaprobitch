"""Canonical C-08 ablation comparison helpers.

Ablation deltas are descriptive selection/coverage diagnostics only. They do not
represent clinical performance or causal effect.
"""
from .a6_validation import A6_ABLATIONS, run_ablations, compare_baseline


def compare(results):
    """Normalize ablation records and report descriptive deltas vs full WGR-CDP."""
    if results is None:
        return {"status": "Data unavailable", "ablations": []}
    records = []
    for name in A6_ABLATIONS:
        if name not in results:
            continue
        row = dict(results[name])
        coverage = row.get("coverage", "Data unavailable")
        records.append({
            "ablation": name,
            "k": row.get("k"),
            "selected": list(row.get("selected", [])),
            "selection_method": row.get("selection_method"),
            "coverage": coverage,
            "ineligible": row.get("ineligible"),
            "unscored": row.get("unscored"),
            "coverage_delta_vs_full": "Data unavailable",
        })
    full = next((r for r in records if r["ablation"] == "full_wgr_cdp"), None)
    if full and isinstance(full.get("coverage"), (int, float)):
        baseline = float(full["coverage"])
        for row in records:
            value = row.get("coverage")
            if isinstance(value, (int, float)):
                row["coverage_delta_vs_full"] = float(value) - baseline
    return {"status": "Available" if records else "Data unavailable", "ablations": records}
