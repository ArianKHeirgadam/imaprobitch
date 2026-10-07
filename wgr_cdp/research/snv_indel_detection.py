"""SNV/INDEL detection and feature-extraction engine.

Consumes called VCF/VCF.GZ records. It does not perform raw-read variant
calling. It produces auditable patient-level features and case/control
statistics using the existing WGR-CDP scanner.
"""
from __future__ import annotations

import csv
import gzip
from collections import defaultdict
from pathlib import Path

from .multires_scanner import exact_scan

POSITIVE_FILTERS = {"PASS", "."}
MISSING = {"", ".", "NA", "N/A", "NULL", "NONE", "DATA UNAVAILABLE"}


def _open_text(path):
    path = Path(path)
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open("r", encoding="utf-8")


def _float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _info_map(raw):
    out = {}
    for item in str(raw or "").split(";"):
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            out[key] = value
        else:
            out[item] = True
    return out


def _format_map(keys, sample):
    values = str(sample or "").split(":")
    return {k: values[i] for i, k in enumerate(keys) if i < len(values)}


def classify_variant(ref, alt):
    ref, alt = str(ref).upper(), str(alt).upper()
    if not ref or not alt or alt.startswith("<") or "[" in alt or "]" in alt:
        return None
    if len(ref) == 1 and len(alt) == 1:
        return "SNV"
    if len(ref) != len(alt):
        return "INDEL"
    return None


def parse_vcf(path, sample_id=None, group=None, min_depth=None, min_vaf=None):
    """Extract explicit SNV/INDEL observations from a VCF/VCF.GZ file."""
    rows = []
    path = Path(path)
    inferred_sample = sample_id or path.name.replace(".vcf.gz", "").replace(".vcf", "")
    with _open_text(path) as handle:
        samples = []
        for line in handle:
            line = line.rstrip("\r\n")
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                header = line.split("\t")
                samples = header[9:]
                continue
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) < 8:
                continue
            chrom, pos, vid, ref, alts, qual, filt, info_raw = fields[:8]
            if filt not in POSITIVE_FILTERS:
                continue
            info = _info_map(info_raw)
            fmt_keys = fields[8].split(":") if len(fields) > 8 else []
            sample_values = fields[9:] if len(fields) > 9 else []
            observations = (
                [(name, _format_map(fmt_keys, sample)) for name, sample in zip(samples, sample_values)]
                if sample_values and samples else [(inferred_sample, {})]
            )
            for observed_sample, fmt in observations:
                gt = fmt.get("GT")
                dp = _float(fmt.get("DP") or info.get("DP"))
                ad_raw = fmt.get("AD") or info.get("AD")
                ad = []
                if ad_raw not in MISSING:
                    for x in str(ad_raw).split(","):
                        value = _float(x)
                        ad.append(value if value is not None else 0.0)
                for alt_index, alt in enumerate(str(alts).split(","), start=1):
                    variant_type = classify_variant(ref, alt)
                    if variant_type is None:
                        continue
                    vaf = None
                    if len(ad) > alt_index and sum(ad) > 0:
                        vaf = ad[alt_index] / sum(ad)
                    elif fmt.get("AF") not in MISSING:
                        raw_af = str(fmt.get("AF")).split(",")
                        vaf = _float(raw_af[min(alt_index - 1, len(raw_af) - 1)])
                    elif info.get("AF") not in MISSING:
                        raw_af = str(info.get("AF")).split(",")
                        vaf = _float(raw_af[min(alt_index - 1, len(raw_af) - 1)])
                    if min_depth is not None and (dp is None or dp < min_depth):
                        continue
                    if min_vaf is not None and (vaf is None or vaf < min_vaf):
                        continue
                    # Interpret genotype explicitly: any called non-reference allele is
                    # detected; reference-only is negative; missing genotype is unavailable.
                    gt_tokens = set()
                    if gt not in MISSING:
                        gt_tokens = {token for token in str(gt).replace("|", "/").split("/") if token not in MISSING}
                    if not gt_tokens:
                        status = "Data unavailable"
                    elif all(token == "0" for token in gt_tokens):
                        status = "Not detected"
                    else:
                        status = "Detected"
                    rows.append({
                        "patient": observed_sample,
                        "group": group or "unknown",
                        "region": f"{chrom}:{int(pos)}-{int(pos) + max(len(ref), len(alt)) - 1}",
                        "feature_type": variant_type,
                        "status": status,
                        "value": f"{ref}>{alt}",
                        "chrom": chrom,
                        "pos": int(pos),
                        "ref": ref,
                        "alt": alt,
                        "variant_id": vid if vid != "." else f"{chrom}:{pos}:{ref}>{alt}",
                        "filter": filt,
                        "qual": _float(qual),
                        "depth": dp,
                        "vaf": vaf,
                        "gene": info.get("GENE") or info.get("SYMBOL") or info.get("Gene"),
                        "source_file": str(path),
                    })
    return rows


def load_cohort(paths, group, min_depth=None, min_vaf=None):
    rows = []
    for item in paths:
        rows.extend(parse_vcf(item, group=group, min_depth=min_depth, min_vaf=min_vaf))
    return rows


def detect_snv_indel(cancer_paths, healthy_paths, alpha=0.05, min_depth=None, min_vaf=None):
    rows = load_cohort(cancer_paths, "cancer", min_depth, min_vaf)
    rows.extend(load_cohort(healthy_paths, "healthy", min_depth, min_vaf))
    results = exact_scan(rows, alpha=alpha)
    results = [r for r in results if r["feature_type"] in {"SNV", "INDEL"}]
    for row in results:
        row["detection_engine"] = "SNV_INDEL"
        row["status"] = "Detected" if row.get("case_carriers", 0) else "Data unavailable"
    return {"rows": rows, "results": results, "status": "PASS" if rows else "Data unavailable"}


def write_detection_artifacts(result, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    obs_fields = ["patient", "group", "region", "feature_type", "status", "value",
                  "variant_id", "qual", "depth", "vaf", "gene", "source_file"]
    with (output / "snv_indel_observations.csv").open("w", encoding="utf-8", newline="") as h:
        writer = csv.DictWriter(h, fieldnames=obs_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result["rows"])
    result_fields = sorted({k for row in result["results"] for k in row})
    with (output / "snv_indel_detection.csv").open("w", encoding="utf-8", newline="") as h:
        writer = csv.DictWriter(h, fieldnames=result_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result["results"])
    return result
