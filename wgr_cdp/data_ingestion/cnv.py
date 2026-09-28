"""Real CNV segment ingestion for WGR-CDP."""
import csv
from pathlib import Path

def _norm_key(value):
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")

def _first(row, names, default=None):
    for name in names:
        if name in row and str(row[name]).strip():
            return row[name]
    return default

def _normalize_chrom(value):
    chrom = str(value or "").strip()
    if not chrom:
        raise ValueError("CNV chromosome is required")
    return chrom[3:] if chrom.lower().startswith("chr") else chrom

def _number(value, field):
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid CNV {field}: {value}") from exc

def classify_event(copy_number=None, log2_ratio=None, gain_log2=0.25, loss_log2=-0.25):
    if copy_number not in (None, ""):
        cn = _number(copy_number, "copy_number")
        if cn > 2: return "GAIN"
        if cn < 2: return "LOSS"
        return "NEUTRAL"
    if log2_ratio not in (None, ""):
        lr = _number(log2_ratio, "log2_ratio")
        if lr >= gain_log2: return "GAIN"
        if lr <= loss_log2: return "LOSS"
        return "NEUTRAL"
    return "Data unavailable"

def read_cnv_segments(path, group=None, gain_log2=0.25, loss_log2=-0.25):
    path = Path(path)
    if not path.exists():
        raise ValueError(f"CNV file does not exist: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        delimiter = "\t" if "\t" in sample and "," not in sample else ","
        reader = csv.DictReader(handle, delimiter=delimiter)
        raw_rows = list(reader)
    if not reader.fieldnames:
        raise ValueError("CNV file has no header")
    rows = []
    for raw in raw_rows:
        row = {_norm_key(k): v for k, v in raw.items()}
        sample_id = _first(row, ("sample_id", "sample", "patient"))
        chrom = _first(row, ("chromosome", "chrom", "chr"))
        start = _first(row, ("start", "start_position"))
        end = _first(row, ("end", "end_position"))
        if any(x in (None, "") for x in (sample_id, chrom, start, end)):
            raise ValueError("CNV rows require sample_id, chromosome, start, and end")
        start_i, end_i = int(_number(start, "start")), int(_number(end, "end"))
        if start_i < 1 or end_i < start_i:
            raise ValueError(f"invalid CNV interval: {chrom}:{start}-{end}")
        copy_number = _first(row, ("copy_number", "copynumber", "cn"))
        log2_ratio = _first(row, ("log2_ratio", "log2", "log2r", "segment_mean"))
        explicit = str(_first(row, ("event_type", "status", "event"), "") or "").strip().upper()
        event_type = explicit if explicit in {"GAIN", "LOSS", "NEUTRAL"} else classify_event(copy_number, log2_ratio, gain_log2, loss_log2)
        genes = _first(row, ("genes", "gene", "gene_symbol", "gene_symbols"))
        chrom_norm = _normalize_chrom(chrom)
        rows.append({
            "sample_id": str(sample_id).strip(),
            "group": str(group or _first(row, ("group", "cohort"), "")).strip(),
            "stage": str(_first(row, ("stage", "cancer_stage"), "") or "").strip(),
            "chrom": chrom_norm, "start": start_i, "end": end_i,
            "region": f"{chrom_norm}:{start_i}-{end_i}",
            "copy_number": copy_number if copy_number not in (None, "") else None,
            "log2_ratio": log2_ratio if log2_ratio not in (None, "") else None,
            "event_type": event_type,
            "genes": str(genes).strip() if genes not in (None, "") else None,
            "feature_type": "CNV",
            "status": "Detected" if event_type in {"GAIN", "LOSS"} else ("Not detected" if event_type == "NEUTRAL" else "Data unavailable"),
        })
    return rows
