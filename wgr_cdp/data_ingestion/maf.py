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
    required = {
        "Chromosome", "Start_Position", "Reference_Allele",
        "Tumor_Seq_Allele2", "Tumor_Sample_Barcode",
    }
    with _open(path) as handle:
        header = None
        data_lines = []
        for raw in handle:
            line = raw.rstrip("\r\n")
            if not line.strip():
                continue
            fields = line.split("\t")
            # GDC/TCGA MAF files may have metadata/comment lines before the
            # tab-delimited header. Detect the real header by required fields.
            if header is None:
                if required.issubset(set(fields)):
                    header = fields
                    data_lines.append(raw)
                continue
            # Ignore comment/metadata lines that occur after the header.
            if line.startswith("#"):
                continue
            data_lines.append(raw)
        if header is None:
            raise ValueError("MAF file has no detectable header")
        reader = csv.DictReader(data_lines, fieldnames=header, delimiter="\t")
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


def qc_vcf_adapter(path):
    """Run structural QC on a WGR-CDP adapter VCF."""
    path = Path(path)
    result = {
        "path": str(path),
        "status": "Data unavailable",
        "record_count": 0,
        "invalid_record_count": 0,
        "missing_source_tag_count": 0,
        "normalization_required": True,
    }
    if not path.exists():
        return result
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            result["record_count"] += 1
            fields = line.split("\t")
            invalid = len(fields) < 8
            if not invalid:
                try:
                    invalid = int(fields[1]) < 1
                except (TypeError, ValueError):
                    invalid = True
            if not invalid and (not fields[3] or not fields[4]):
                invalid = True
            if invalid:
                result["invalid_record_count"] += 1
            if "SOURCE=GDC_MASKED_SOMATIC_MAF" not in fields[7] if len(fields) >= 8 else True:
                result["missing_source_tag_count"] += 1
    result["status"] = (
        "PASS"
        if result["record_count"] > 0
        and result["invalid_record_count"] == 0
        and result["missing_source_tag_count"] == 0
        else "FAIL" if result["invalid_record_count"] > 0
        or result["missing_source_tag_count"] > 0
        else "Data unavailable"
    )
    return result

def convert_maf_directory_to_vcf(input_dir, output_dir, *, pattern="*.maf.gz"):
    """Convert all MAF files in a directory and emit a batch provenance manifest."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    files = sorted(input_dir.glob(pattern))
    results = []
    for source in files:
        converted = convert_maf_to_vcf(
            source,
            output_dir,
            prefix=source.name.replace(".maf.gz", "").replace(".maf", ""),
        )
        qc = []
        for item in converted.get("files") or []:
            qc.append(qc_vcf_adapter(item["path"]))
        results.append({
            "source_file": str(source),
            "source_format": "GDC masked somatic MAF",
            "conversion": converted,
            "qc": qc,
            "normalization_required": True,
        })
    files_with_outputs = sum(bool(r["conversion"].get("files")) for r in results)
    qc_items = [item for r in results for item in r["qc"]]
    status = (
        "PASS"
        if results and files_with_outputs == len(results)
        and qc_items and all(item["status"] == "PASS" for item in qc_items)
        else "Data unavailable" if not results else "CONDITIONAL"
    )
    return {
        "schema_version": "A13-MAF-BATCH-1",
        "status": status,
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "input_file_count": len(files),
        "converted_file_count": files_with_outputs,
        "sample_count": sum(r["conversion"].get("sample_count", 0) for r in results),
        "variant_record_count": sum(r["conversion"].get("record_count", 0) for r in results),
        "qc_record_count": sum(item["record_count"] for item in qc_items),
        "qc_invalid_record_count": sum(item["invalid_record_count"] for item in qc_items),
        "qc_missing_source_tag_count": sum(item["missing_source_tag_count"] for item in qc_items),
        "normalization_required": True,
        "results": results,
    }
