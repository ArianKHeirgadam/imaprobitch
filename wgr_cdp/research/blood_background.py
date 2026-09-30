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
    for feature, source_rows in grouped.items():
        output[feature] = {}
        for source in sources:
            values = source_rows.get(source, [])
            output[feature][source] = {"n": len(values), "mean": sum(values) / len(values) if values else None, "max": max(values) if values else None, "status": "Available" if values else "Data unavailable"}
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