"""A15: CNV detection and validation with separate event/dosage contracts."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from wgr_cdp.cohort_analysis.statistics import fisher_exact_2x2
from wgr_cdp.data_ingestion.cnv import read_cnv_segments
from wgr_cdp.evaluation.multiple_testing import benjamini_hochberg
from wgr_cdp.research.cnv_statistics import describe_cnv_statistics

EVENTS = {"GAIN", "LOSS"}
OBSERVED_EVENTS = {"GAIN", "LOSS", "NEUTRAL"}

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _group(row):
    value = str(row.get("group", "")).strip().lower()
    if value in {"case", "cancer", "tumor"}: return "case"
    if value in {"control", "comparator", "normal", "healthy"}: return "comparator"
    return "Data unavailable"

def _region(row):
    return f"{row['chrom']}:{int(row['start'])}-{int(row['end'])}"

def _float_or_none(value):
    if value in (None, ""): return None
    try: return float(value)
    except (TypeError, ValueError): return None

def _sample_ids(rows, group):
    return {str(r["sample_id"]) for r in rows if _group(r) == group}

def _explicit_region_rows(rows, region):
    return [r for r in rows if _region(r) == region and r.get("event_type") in OBSERVED_EVENTS]

def compare_cnv_events_and_dosage(rows, permutations=999, seed=42):
    """Compare categorical CNV carriers and continuous dosage independently."""
    if not rows: raise ValueError("no CNV observations supplied")
    case_samples = _sample_ids(rows, "case")
    comparator_samples = _sample_ids(rows, "comparator")
    if not case_samples or not comparator_samples:
        raise ValueError("CNV comparison requires both case/tumor and comparator observations")
    regions = sorted({_region(r) for r in rows if r.get("event_type") in EVENTS})
    event_rows, dosage_rows = [], []
    for region in regions:
        observed = _explicit_region_rows(rows, region)
        case_observed = {str(r["sample_id"]) for r in observed if _group(r) == "case"}
        comparator_observed = {str(r["sample_id"]) for r in observed if _group(r) == "comparator"}
        for event_type in ("GAIN", "LOSS"):
            carriers_case = {str(r["sample_id"]) for r in observed if _group(r) == "case" and r.get("event_type") == event_type}
            carriers_comparator = {str(r["sample_id"]) for r in observed if _group(r) == "comparator" and r.get("event_type") == event_type}
            a, b = len(carriers_case), len(carriers_comparator)
            case_n, comparator_n = len(case_observed), len(comparator_observed)
            c, d = case_n - a, comparator_n - b
            cf = a / case_n if case_n else None
            hf = b / comparator_n if comparator_n else None
            diff = cf - hf if cf is not None and hf is not None else None
            event_rows.append({
                "feature": f"{region}|{event_type}", "region": region, "event_type": event_type,
                "case_carriers": a, "comparator_carriers": b, "case_n": case_n, "comparator_n": comparator_n,
                "case_frequency": cf, "comparator_frequency": hf, "frequency_difference": diff,
                "effect_size": abs(diff) if diff is not None else None,
                "p_value": fisher_exact_2x2(a, b, c, d) if case_n and comparator_n else None,
                "statistical_method": "Fisher exact test on explicit event carriers",
                "denominator_semantics": "explicit region observation only; missing segment is Data unavailable, not NEUTRAL",
            })
        case_values = [v for r in observed if _group(r) == "case" for v in [_float_or_none(r.get("log2_ratio"))] if v is not None]
        comparator_values = [v for r in observed if _group(r) == "comparator" for v in [_float_or_none(r.get("log2_ratio"))] if v is not None]
        dosage = describe_cnv_statistics(case_values, comparator_values, permutations=permutations, seed=seed)
        dosage_rows.append({
            "feature": region, "region": region,
            "case_dosage_n": len(case_values), "comparator_dosage_n": len(comparator_values),
            "case_mean_log2": sum(case_values) / len(case_values) if case_values else None,
            "comparator_mean_log2": sum(comparator_values) / len(comparator_values) if comparator_values else None,
            "mean_difference": dosage["mean_difference"], "effect_size": dosage["effect_size"],
            "p_value": dosage["p_value"], "statistical_method": dosage["statistical_test"],
            "permutations": dosage["permutations"], "seed": dosage["seed"],
            "denominator_semantics": "explicit numeric dosage only; missing dosage is Data unavailable",
        })
    event_p = [r["p_value"] for r in event_rows if r["p_value"] is not None]
    event_q = benjamini_hochberg(event_p) if event_p else []
    i = 0
    for row in event_rows:
        row["q_value"] = event_q[i] if row["p_value"] is not None else None
        if row["p_value"] is not None: i += 1
    dosage_p = [r["p_value"] for r in dosage_rows if r["p_value"] is not None]
    dosage_q = benjamini_hochberg(dosage_p) if dosage_p else []
    i = 0
    for row in dosage_rows:
        row["q_value"] = dosage_q[i] if row["p_value"] is not None else None
        if row["p_value"] is not None: i += 1
    return {"event_rows": event_rows, "dosage_rows": dosage_rows,
            "case_sample_count": len(case_samples), "comparator_sample_count": len(comparator_samples),
            "region_count": len(regions)}

def validate_cnv_cohort(input_path, output_dir, *, alpha=0.05, permutations=999, seed=42, metadata_path=None):
    """Run A15 validation and write provenance/statistical artifacts."""
    source, output = Path(input_path), Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        files = sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() in {".csv", ".tsv", ".txt"})
        if not files: raise ValueError(f"no CNV tabular files found: {source}")
        rows, provenance = [], []
        for path in files:
            file_rows = read_cnv_segments(path); rows.extend(file_rows)
            provenance.append({"path": str(path), "sha256": _sha256(path), "row_count": len(file_rows)})
    else:
        if not source.exists(): raise ValueError(f"CNV input does not exist: {source}")
        rows = read_cnv_segments(source)
        provenance = [{"path": str(source), "sha256": _sha256(source), "row_count": len(rows)}]
    result = {
        "schema_version": "A15-CNV-VALIDATION-1", "status": "PASS", "modality": "CNV",
        "scientific_role": "research_cohort_validation", "input_file_count": len(provenance),
        "input_record_count": len(rows), "source_provenance": provenance, "alpha": float(alpha),
        "permutations": int(permutations), "seed": int(seed),
        "metadata_path": str(metadata_path) if metadata_path else None,
        "healthy_control_status": "Data unavailable",
        "healthy_control_semantics": "A comparator/matched normal is not relabelled as an independent healthy population.",
    }
    if metadata_path:
        import csv
        metadata_file = Path(metadata_path)
        if not metadata_file.exists():
            raise ValueError(f"CNV metadata file does not exist: {metadata_file}")
        with metadata_file.open(encoding="utf-8-sig", newline="") as handle:
            metadata_rows = list(csv.DictReader(handle))
        mapping = {}
        for item in metadata_rows:
            sid = str(item.get("sample_id") or item.get("sample") or item.get("gdc_aliquot_id") or "").strip()
            grp = str(item.get("group") or item.get("cohort") or "").strip()
            if sid and grp:
                mapping[sid] = grp
        for row in rows:
            if str(row.get("group", "")).strip() == "" and row["sample_id"] in mapping:
                row["group"] = mapping[row["sample_id"]]
        result["group_metadata_source"] = str(metadata_file)
    else:
        result["group_metadata_source"] = "inline CNV group column"
    groups = {_group(r) for r in rows}
    if "case" not in groups or "comparator" not in groups:
        result.update({"status": "CONDITIONAL", "comparison_status": "Data unavailable",
                       "reason": "Both tumor/case and comparator observations are required; no biological result is inferred from a missing group."})
        (output / "a15_cnv_validation.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        return result
    comparison = compare_cnv_events_and_dosage(rows, permutations=permutations, seed=seed)
    import csv
    def write_csv(name, values):
        path = output / name
        fields = list(values[0].keys()) if values else ["feature"]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore"); writer.writeheader(); writer.writerows(values)
    write_csv("cnv_event_statistics.csv", comparison["event_rows"])
    write_csv("cnv_dosage_statistics.csv", comparison["dosage_rows"])
    event_rows, dosage_rows = comparison["event_rows"], comparison["dosage_rows"]
    result.update({
        "comparison_status": "PASS", "case_sample_count": comparison["case_sample_count"],
        "comparator_sample_count": comparison["comparator_sample_count"], "region_count": comparison["region_count"],
        "event_test_count": len(event_rows), "dosage_test_count": len(dosage_rows),
        "event_significant_count": sum(r["q_value"] is not None and r["q_value"] <= alpha for r in event_rows),
        "dosage_significant_count": sum(r["q_value"] is not None and r["q_value"] <= alpha for r in dosage_rows),
        "event_vs_dosage_contract": "SEPARATE",
        "status_semantics": "event carrier and continuous dosage statistics are separate analysis contracts.",
    })
    (output / "a15_cnv_validation.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return result
