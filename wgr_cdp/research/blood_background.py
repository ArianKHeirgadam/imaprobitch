"""Source-specific blood-background estimation and filtering."""
from __future__ import annotations
from collections import defaultdict

BACKGROUND_SOURCES = ("healthy_plasma", "wbc", "pon", "gnomad", "chip", "observed")

def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _source_value(row, source):
    value = row.get(source)
    if value is None and source == "healthy_plasma":
        value = row.get("blood_background")
    return _as_float(value)

def estimate_background(rows, key="region", sources=None):
    """Estimate each background source independently."""
    sources = tuple(sources or BACKGROUND_SOURCES)
    if any(source not in BACKGROUND_SOURCES for source in sources):
        raise ValueError("unsupported blood-background source")
    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        feature = str(row.get(key, ""))
        for source in sources:
            value = _source_value(row, source)
            if value is not None:
                grouped[feature][source].append(value)
    output = {}
    # Emit every observed feature even when all requested background sources
    # are unavailable. Missing source evidence is explicit, never negative.
    observed_features = {str(row.get(key, "")) for row in rows}
    for feature in sorted(observed_features):
        source_rows = grouped.get(feature, {})
        output[feature] = {}
        for source in sources:
            values = source_rows.get(source, [])
            output[feature][source] = {
                "n": len(values),
                "mean": sum(values) / len(values) if values else None,
                "max": max(values) if values else None,
                "status": "Available" if values else "Data unavailable",
            }
    return output


def build_pon(rows, key="region", normal_groups=("control", "healthy", "normal")):
    """Build a source-observation-aware Panel of Normals from explicit normal calls."""
    positives = {"detected", "positive", "present", "variant detected"}
    negatives = {"not detected", "not_detected", "negative", "reference", "wildtype", "wild type", "no variant", "no_variant"}
    groups = {str(g).strip().lower() for g in normal_groups}
    observed = defaultdict(set)
    carriers = defaultdict(set)
    for row in rows:
        if str(row.get("group", "")).strip().lower() not in groups:
            continue
        feature = str(row.get(key, ""))
        patient = str(row.get("patient") or row.get("sample_id") or "")
        if not patient or not feature:
            continue
        status = str(row.get("status", "")).strip().lower()
        if status in positives or status in negatives:
            observed[feature].add(patient)
            if status in positives:
                carriers[feature].add(patient)
    features = sorted(set(observed) | {str(r.get(key, "")) for r in rows if str(r.get(key, ""))})
    out = {}
    for feature in features:
        n = len(observed.get(feature, set()))
        k = len(carriers.get(feature, set()))
        out[feature] = {
            "observed_samples": n,
            "carrier_samples": k,
            "frequency": (k / n) if n else None,
            "status": "Available" if n else "Data unavailable",
        }
    return out


def annotate_pon(candidates, pon, key="region"):
    """Attach PoN frequency without treating unavailable PoN as zero."""
    output = []
    for row in candidates:
        x = dict(row)
        feature = str(x.get(key) or x.get("feature") or "")
        item = pon.get(feature, {})
        x["pon_frequency"] = item.get("frequency")
        x["pon_status"] = item.get("status", "Data unavailable")
        output.append(x)
    return output

def _row_background(row, background):
    key = str(row.get("region") or row.get("feature") or "")
    source_data = background.get(key, {})
    values = [item.get("max") for item in source_data.values() if isinstance(item, dict) and item.get("max") is not None]
    return max(values) if values else None

def filter_candidates(candidates, background, max_background=0.10):
    """Filter by available background; unavailable is not negative evidence."""
    kept, rejected = [], []
    for row in candidates:
        x = dict(row)
        bg = _row_background(x, background)
        x["blood_background_max"] = bg
        x["blood_background_status"] = "Data unavailable" if bg is None else ("pass" if bg <= max_background else "fail")
        x["blood_background_safety"] = "Data unavailable" if bg is None else max(0.0, min(1.0, 1.0 - bg))
        (kept if bg is None or bg <= max_background else rejected).append(x)
    return kept, rejected

def annotate_background_sources(candidates, background):
    output = []
    for row in candidates:
        x = dict(row)
        key = str(x.get("region") or x.get("feature") or "")
        source_data = background.get(key, {})
        x["blood_background_sources"] = {source: dict(source_data.get(source, {"n": 0, "mean": None, "max": None, "status": "Data unavailable"})) for source in BACKGROUND_SOURCES}
        output.append(x)
    return output