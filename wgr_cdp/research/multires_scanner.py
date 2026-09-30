"""Feature-specific multi-resolution WGR-CDP discovery scanner.

Implements 5 Mb -> 1 Mb -> 100 kb -> 10 kb -> 1 kb -> base/breakpoint
with feature-specific coarse statistics, effect sizes, screening, neighbor
expansion, and exact final validation.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from math import comb, isfinite
from statistics import mean

from .statistics import benjamini_hochberg, fisher_exact_2x2

RESOLUTIONS = (5_000_000, 1_000_000, 100_000, 10_000, 1_000, 1)
LABELS = {5_000_000: "5Mb", 1_000_000: "1Mb", 100_000: "100kb", 10_000: "10kb", 1_000: "1kb", 1: "base"}
BINARY_FEATURES = {"SNV", "INDEL"}
CONTINUOUS_FEATURES = {"CNV", "METHYLATION", "MITOCHONDRIAL"}
SUPPORTED_FEATURES = BINARY_FEATURES | CONTINUOUS_FEATURES | {"SV", "FRAGMENTOMICS"}


def _parts(region):
    chrom, span = str(region).split(":", 1)
    start, end = span.split("-", 1)
    start, end = int(start), int(end)
    if start < 1 or end < start:
        raise ValueError(f"invalid genomic interval: {region}")
    return chrom, start, end


def _bin(region, size):
    chrom, start, end = _parts(region)
    first = ((start - 1) // size) * size + 1
    last = ((max(start, end) - 1) // size) * size + 1
    return [f"{chrom}:{x}-{x + size - 1}" for x in range(first, last + 1, size)]


def _group(row):
    return str(row.get("group", "")).strip().lower()


def _patients(rows, groups):
    return {str(r["patient"]) for r in rows if _group(r) in groups}


def _overlaps(a, b):
    ca, sa, ea = _parts(a)
    cb, sb, eb = _parts(b)
    return ca == cb and sa <= eb and sb <= ea


def _feature_type(row):
    return str(row.get("feature_type", "SNV")).strip().upper()


def _numeric(row, keys):
    for key in keys:
        value = row.get(key)
        if value in (None, ""):
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if isfinite(value):
            return value
    return None


def _detected(row):
    return str(row.get("status", "")).strip().lower() == "detected"


def _patient_binary_values(rows, patients):
    values = {p: 0 for p in patients}
    for row in rows:
        patient = str(row["patient"])
        if patient in values and _detected(row):
            values[patient] = 1
    return values


def _patient_numeric_values(rows, patients, feature_type):
    values = defaultdict(list)
    for row in rows:
        patient = str(row["patient"])
        if patient not in patients:
            continue
        if feature_type == "CNV":
            keys = ("log2_ratio", "segment_mean")
        elif feature_type == "METHYLATION":
            keys = ("beta", "m_value", "value")
        elif feature_type == "MITOCHONDRIAL":
            keys = ("heteroplasmy", "copy_number_mt", "value")
        else:
            keys = ("value",)
        value = _numeric(row, keys)
        if value is not None:
            values[patient].append(value)
    return {p: mean(v) for p, v in values.items() if v}


def _permutation_pvalue(case_values, control_values):
    """Two-sided exact permutation p-value for patient-level continuous data."""
    case_values = [float(x) for x in case_values]
    control_values = [float(x) for x in control_values]
    if not case_values or not control_values:
        return 1.0

    observed = abs(mean(case_values) - mean(control_values))
    pooled = case_values + control_values
    n1 = len(case_values)
    total = comb(len(pooled), n1)

    if total <= 100_000:
        extreme = 0
        for indices in combinations(range(len(pooled)), n1):
            selected = set(indices)
            a = [pooled[i] for i in indices]
            b = [pooled[i] for i in range(len(pooled)) if i not in selected]
            if abs(mean(a) - mean(b)) >= observed - 1e-15:
                extreme += 1
        return min(1.0, extreme / total)

    seed = 0x9E3779B9
    extreme = 0
    iterations = 100_000
    for _ in range(iterations):
        order = list(range(len(pooled)))
        for i in range(len(order) - 1, 0, -1):
            seed = (1664525 * seed + 1013904223) & 0xFFFFFFFF
            j = seed % (i + 1)
            order[i], order[j] = order[j], order[i]
        a = [pooled[i] for i in order[:n1]]
        b = [pooled[i] for i in order[n1:]]
        if abs(mean(a) - mean(b)) >= observed - 1e-15:
            extreme += 1
    return min(1.0, (extreme + 1) / (iterations + 1))


def _binary_stats(sub, cases, controls):
    case_values = _patient_binary_values(sub, cases)
    control_values = _patient_binary_values(sub, controls)
    a = sum(case_values.values())
    b = sum(control_values.values())
    cf = a / len(cases)
    hf = b / len(controls)
    return {
        "case_frequency": cf,
        "control_frequency": hf,
        "effect_size": abs(cf - hf),
        "p_value": fisher_exact_2x2(a, b, len(cases) - a, len(controls) - b),
        "case_carriers": a,
        "control_carriers": b,
    }


def _continuous_stats(sub, cases, controls, feature_type):
    case_values = _patient_numeric_values(sub, cases, feature_type)
    control_values = _patient_numeric_values(sub, controls, feature_type)
    if not case_values or not control_values:
        return {
            "case_frequency": None,
            "control_frequency": None,
            "effect_size": 0.0,
            "p_value": 1.0,
            "case_mean": None,
            "control_mean": None,
            "case_carriers": len(case_values),
            "control_carriers": len(control_values),
        }

    case_mean = mean(case_values.values())
    control_mean = mean(control_values.values())
    return {
        "case_frequency": None,
        "control_frequency": None,
        "effect_size": abs(case_mean - control_mean),
        "p_value": _permutation_pvalue(
            list(case_values.values()), list(control_values.values())
        ),
        "case_mean": case_mean,
        "control_mean": control_mean,
        "case_carriers": len(case_values),
        "control_carriers": len(control_values),
    }


def _feature_stats(sub, cases, controls, feature_type):
    if feature_type in BINARY_FEATURES:
        return _binary_stats(sub, cases, controls)
    if feature_type in CONTINUOUS_FEATURES:
        return _continuous_stats(sub, cases, controls, feature_type)
    return _binary_stats(sub, cases, controls)


def _result(region, feature_type, stats, resolution, parent_region=None):
    return {
        "region": region,
        "feature_type": feature_type,
        "resolution": LABELS[resolution],
        "resolution_bp": resolution,
        "parent_region": parent_region,
        **stats,
    }


def exact_scan(rows, alpha=0.05):
    """Exact native-resolution comparison for all supplied feature types."""
    cases = _patients(rows, {"case", "cancer", "tumor"})
    controls = _patients(rows, {"control", "healthy", "normal"})
    if not cases or not controls:
        return []

    features = sorted({(str(r["region"]), _feature_type(r)) for r in rows})
    out = []
    for region, feature_type in features:
        sub = [
            r for r in rows
            if str(r["region"]) == region and _feature_type(r) == feature_type
        ]
        out.append(
            _result(
                region,
                feature_type,
                _feature_stats(sub, cases, controls, feature_type),
                1,
            )
        )

    q_values = benjamini_hochberg([r["p_value"] for r in out])
    for result, q_value in zip(out, q_values):
        result["q_value"] = q_value
        result["significant"] = q_value <= alpha
        result["exact_checked"] = True
    return out


def _coarse_region_stats(rows, region, feature_type):
    sub = [
        row for row in rows
        if _feature_type(row) == feature_type and _overlaps(row["region"], region)
    ]
    cases = _patients(sub, {"case", "cancer", "tumor"})
    controls = _patients(sub, {"control", "healthy", "normal"})
    if not cases or not controls:
        return None

    stats = _feature_stats(sub, cases, controls, feature_type)

    if feature_type in BINARY_FEATURES:
        span_bp = max(1, _parts(region)[2] - _parts(region)[1] + 1)
        case_events = sum(
            1 for row in sub
            if str(row["patient"]) in cases and _detected(row)
        )
        control_events = sum(
            1 for row in sub
            if str(row["patient"]) in controls and _detected(row)
        )
        stats["case_variant_density"] = case_events / (span_bp / 1_000_000)
        stats["control_variant_density"] = control_events / (span_bp / 1_000_000)
        stats["variant_density_difference"] = abs(
            stats["case_variant_density"] - stats["control_variant_density"]
        )
    return stats


def _neighbor_regions(region, size, neighbor_k):
    chrom, start, _ = _parts(region)
    center = ((start - 1) // size) * size
    regions = []
    for offset in range(-neighbor_k, neighbor_k + 1):
        begin = center + offset * size + 1
        if begin >= 1:
            regions.append(f"{chrom}:{begin}-{begin + size - 1}")
    return regions


def coarse_to_fine_scan(rows, alpha=0.05, effect_threshold=0.10, neighbor_k=1):
    """Hierarchical coarse-to-fine discovery followed by exact validation."""
    if neighbor_k < 0:
        raise ValueError("neighbor_k must be >= 0")
    if effect_threshold < 0:
        raise ValueError("effect_threshold must be >= 0")

    exact = exact_scan(rows, alpha=alpha)
    feature_types = sorted({_feature_type(r) for r in rows})

    active = set()
    for row in rows:
        for region in _bin(row["region"], RESOLUTIONS[0]):
            active.add((region, _feature_type(row), None))

    lineage = []
    retained = set()

    for level_index, size in enumerate(RESOLUTIONS[:-1]):
        next_active = set()
        for region, feature_type, parent_region in sorted(active):
            stats = _coarse_region_stats(rows, region, feature_type)
            if stats is None:
                continue

            if feature_type in BINARY_FEATURES:
                density_effect = float(stats.get("variant_density_difference") or 0.0)
                screening_effect = max(
                    float(stats["effect_size"]),
                    density_effect / (1.0 + density_effect),
                )
            else:
                screening_effect = float(stats["effect_size"])

            retained_here = screening_effect >= effect_threshold
            lineage.append({
                "resolution": LABELS[size],
                "resolution_bp": size,
                "region": region,
                "feature_type": feature_type,
                "effect_size": float(stats["effect_size"]),
                "screening_effect": screening_effect,
                "p_value": float(stats["p_value"]),
                "retained": retained_here,
                "parent_region": parent_region,
                "case_frequency": stats.get("case_frequency"),
                "control_frequency": stats.get("control_frequency"),
                "case_mean": stats.get("case_mean"),
                "control_mean": stats.get("control_mean"),
                "case_variant_density": stats.get("case_variant_density"),
                "control_variant_density": stats.get("control_variant_density"),
                "variant_density_difference": stats.get("variant_density_difference"),
            })

            if not retained_here:
                continue

            retained.add((region, feature_type))
            child_size = RESOLUTIONS[level_index + 1]
            for child in _neighbor_regions(region, child_size, neighbor_k):
                next_active.add((child, feature_type, region))
        active = next_active
        if not active:
            break

    final_active = active
    final = [
        {**result, "exact_checked": True}
        for result in exact
        if any(
            feature_type == result["feature_type"]
            and _overlaps(result["region"], region)
            for region, feature_type, _parent in final_active
        )
    ]

    final_q = benjamini_hochberg([r["p_value"] for r in final])
    for result, q_value in zip(final, final_q):
        result["q_value"] = q_value
        result["significant"] = q_value <= alpha

    return {
        "resolutions": [LABELS[x] for x in RESOLUTIONS],
        "exact": exact,
        "lineage": lineage,
        "retained_regions": sorted(retained),
        "exact_checked": len(final),
        "final_active_regions": sorted((region, feature_type) for region, feature_type, _parent in final_active),
        "final": final,
        "neighbor_k": neighbor_k,
        "effect_threshold": effect_threshold,
        "alpha": alpha,
        "feature_types": feature_types,
    }
