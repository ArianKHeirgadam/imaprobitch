"""GDC somatic MAF -> WGR-CDP adapter VCF.

This adapter is intentionally provenance-preserving: output VCFs are derived
from public masked somatic MAFs, not raw WGS calls. Indels still require
reference-aware normalization after conversion.
"""
from __future__ import annotations

import csv
import gzip
from pathlib import Path

UNAVAILABLE = "Data unavailable"

def _open(path):
    path = Path(path)
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8-sig", newline="")
    return path.open("r", encoding="utf-8-sig", newline="")

def _esc(value):
    text = str(value if value not in (None, "") else UNAVAILABLE)
    return (
        text.replace("%", "%25").replace(";", "%3B")
        .replace("=", "%3D").replace(",", "%2C")
    )

def _first(row, names):
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return None

def read_maf(path):
    with _open(path) as handle:
        reader = csv.DictReader(
            (line for line in handle if not line.startswith("##")),
            delimiter="	",
        )
        if not reader.fieldnames:
            raise ValueError("MAF file has no header")
        required = {
            "Chromosome", "Start_Position", "Reference_Allele",
            "Tumor_Seq_Allele2", "Tumor_Sample_Barcode",
        }
        missing = sorted(required - set(reader.fieldnames))
        if missing:
            raise ValueError("MAF missing required columns: " + ", ".join(missing))
        return list(reader)

def convert_maf_to_vcf(input_path, output_dir, *, prefix="tcga_stad"):
    rows = read_maf(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    by_sample = {}
    for row in rows:
        sample = str(row.get("Tumor_Sample_Barcode") or "").strip()
        chrom = str(row.get("Chromosome") or "").strip()
        ref = str(row.get("Reference_Allele") or "").strip()
        alt = str(row.get("Tumor_Seq_Allele2") or "").strip()
        if not sample or not chrom or not ref or not alt or alt in {".", "-"}:
            continue
        try:
            pos = int(row.get("Start_Position"))
        except (TypeError, ValueError):
            continue
        gene = _first(row, ("Hugo_Symbol", "Gene"))
        consequence = _first(row, ("Variant_Classification", "Consequence"))
        variant_type = _first(row, ("Variant_Type",))
        info = [
            "SOURCE=GDC_MASKED_SOMATIC_MAF",
            f"GENE={_esc(gene)}",
            f"CONSEQUENCE={_esc(consequence)}",
            f"VARIANT_TYPE={_esc(variant_type)}",
        ]
        sample_rows = by_sample.setdefault(sample, set())
        sample_rows.add((chrom, pos, ".", ref, alt, ".", "PASS", ";".join(info)))
    outputs = []
    header = [
        "##fileformat=VCFv4.2",
        "##source=WGR-CDP_MAF_adapter",
        "##reference=Data unavailable",
        '##INFO=<ID=GENE,Number=1,Type=String,Description="Gene from source MAF">',
        '##INFO=<ID=CONSEQUENCE,Number=1,Type=String,Description="MAF variant classification">',
        '##INFO=<ID=VARIANT_TYPE,Number=1,Type=String,Description="Source MAF variant type">',
        '##INFO=<ID=SOURCE,Number=1,Type=String,Description="Provenance of adapter record">',
        "##wgr_cdp_normalization_status=reference_aware_normalization_required",
        "#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO",
    ]
    for index, (sample, records) in enumerate(sorted(by_sample.items())):
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in sample)
        path = output_dir / f"{prefix}.{safe}.vcf"
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write("\n".join(header) + "\n")
            for record in sorted(records):
                handle.write("\t".join(map(str, record)) + "\n")
        outputs.append({
            "sample_id": sample,
            "path": str(path),
            "record_count": len(records),
            "source_format": "GDC masked somatic MAF",
            "normalization_required": True,
        })
    return {
        "schema_version": "A12-MAF-1",
        "status": "Available" if outputs else "Data unavailable",
        "source_file": str(input_path),
        "sample_count": len(outputs),
        "record_count": sum(item["record_count"] for item in outputs),
        "normalization_required": True,
        "files": outputs,
    }
