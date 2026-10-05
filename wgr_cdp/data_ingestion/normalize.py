"""Reference-aware VCF normalization utilities for WGR-CDP.

The normalizer is dependency-free and intentionally conservative:
- requires a reference FASTA for biological normalization;
- validates REF against the reference sequence;
- minimally trims common bases;
- left-aligns simple insertions/deletions in repeat contexts;
- preserves provenance in INFO and audit metadata;
- never claims normalization when the reference is unavailable or mismatched.
"""
from __future__ import annotations

from pathlib import Path
import hashlib


UNAVAILABLE = "Data unavailable"


def read_fasta(path):
    """Load a small/medium FASTA into a chromosome -> sequence mapping."""
    sequences = {}
    name = None
    chunks = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if name is not None:
                    sequences[name] = "".join(chunks).upper()
                name = line[1:].split()[0]
                chunks = []
            else:
                if name is None:
                    raise ValueError("FASTA sequence encountered before a header")
                chunks.append(line)
    if name is not None:
        sequences[name] = "".join(chunks).upper()
    if not sequences:
        raise ValueError("Reference FASTA contains no sequences")
    return sequences


def _resolve_chrom(reference, chrom):
    chrom = str(chrom)
    aliases = [chrom]
    if chrom.startswith("chr"):
        aliases.append(chrom[3:])
    else:
        aliases.append("chr" + chrom)
    for alias in aliases:
        if alias in reference:
            return alias
    return None


def _trim(ref, alt, pos):
    # Keep at least one anchor base in each allele.
    while len(ref) > 1 and len(alt) > 1 and ref[0] == alt[0]:
        ref = ref[1:]
        alt = alt[1:]
        pos += 1
    while len(ref) > 1 and len(alt) > 1 and ref[-1] == alt[-1]:
        ref = ref[:-1]
        alt = alt[:-1]
    return ref, alt, pos


def _left_align_indel(ref_seq, ref, alt, pos):
    # VCF POS is 1-based. For a simple insertion/deletion, the variant can
    # move left through a repeat when the deleted/inserted terminal base equals
    # the immediately preceding reference base.
    while pos > 1 and len(ref) != len(alt):
        prev = ref_seq[pos - 2]
        if len(ref) < len(alt):
            # insertion: A -> AA becomes one-base earlier when the inserted
            # repeat base is the preceding reference base.
            if alt[-1] != prev:
                break
            pos -= 1
            ref = prev
            alt = prev + alt[:-1]
        else:
            # deletion: AA -> A becomes one-base earlier through an A repeat.
            if ref[-1] != prev:
                break
            pos -= 1
            ref = prev + ref[:-1]
            alt = prev
        ref, alt, pos = _trim(ref, alt, pos)
    return ref, alt, pos


def normalize_variant(record, reference=None, strict_reference=True):
    """Normalize one VCF record against a loaded FASTA mapping.

    Returns a new record plus audit fields. One ALT allele is normalized at a
    time, so callers can safely expand multiallelic records.
    """
    required = ("chrom", "pos", "ref", "alt")
    missing = [key for key in required if key not in record]
    if missing:
        raise ValueError(f"Missing variant fields: {', '.join(missing)}")

    chrom = str(record["chrom"])
    pos = int(record["pos"])
    ref = str(record["ref"]).upper()
    alt = str(record["alt"]).upper()

    if pos < 1 or not ref or not alt:
        raise ValueError("Invalid variant coordinates or alleles")

    result = dict(record)
    result.update({
        "chrom": chrom,
        "pos": pos,
        "ref": ref,
        "alt": alt,
        "normalization_status": "reference_aware",
    })

    if reference is None:
        result["normalization_status"] = UNAVAILABLE
        result["reference_validation"] = UNAVAILABLE
        return result

    ref_chrom = _resolve_chrom(reference, chrom)
    if ref_chrom is None:
        result["normalization_status"] = UNAVAILABLE
        result["reference_validation"] = "chromosome_not_found"
        return result

    sequence = reference[ref_chrom]
    end = pos - 1 + len(ref)
    if end > len(sequence):
        result["normalization_status"] = UNAVAILABLE
        result["reference_validation"] = "reference_interval_out_of_bounds"
        return result

    observed = sequence[pos - 1:end]
    if observed != ref:
        result["reference_validation"] = "mismatch"
        result["normalization_status"] = "reference_mismatch"
        if strict_reference:
            return result
        return result

    norm_ref, norm_alt, norm_pos = _trim(ref, alt, pos)
    if len(norm_ref) != len(norm_alt):
        norm_ref, norm_alt, norm_pos = _left_align_indel(
            sequence, norm_ref, norm_alt, norm_pos
        )
        norm_ref, norm_alt, norm_pos = _trim(norm_ref, norm_alt, norm_pos)

    # Validate the final normalized REF as well.
    final_end = norm_pos - 1 + len(norm_ref)
    if final_end > len(sequence) or sequence[norm_pos - 1:final_end] != norm_ref:
        result["normalization_status"] = "normalization_validation_failed"
        result["reference_validation"] = "normalized_ref_mismatch"
        return result

    result.update({
        "pos": norm_pos,
        "ref": norm_ref,
        "alt": norm_alt,
        "reference_validation": "match",
    })
    return result


def _split_info(info):
    return {} if not info or info == "." else {
        item.split("=", 1)[0]: item for item in str(info).split(";") if item
    }


def _add_info(info, key, value):
    items = [item for item in str(info or ".").split(";") if item and item != "."]
    items.append(f"{key}={value}")
    return ";".join(items)


def _sha256(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_vcf(input_path, output_path, reference_fasta, reference_build="GRCh38"):
    """Normalize a dependency-free VCF with a FASTA reference."""
    from wgr_cdp.data_ingestion.vcf import read_vcf

    reference = read_fasta(reference_fasta)
    records = read_vcf(input_path)
    expanded = []
    status_counts = {}

    for record in records:
        alts = record.get("alt") or []
        for alt in alts:
            normalized = normalize_variant(
                {**record, "alt": str(alt).upper()},
                reference=reference,
                strict_reference=True,
            )
            normalized["id"] = record.get("id")
            normalized["info"] = _add_info(
                record.get("info", "."),
                "WGR_NORM",
                normalized["normalization_status"],
            )
            normalized["info"] = _add_info(
                normalized["info"],
                "WGR_REF_CHECK",
                normalized["reference_validation"],
            )
            normalized["info"] = _add_info(
                normalized["info"],
                "WGR_ORIG",
                f"{record['chrom']}:{int(record['pos'])}:{record['ref']}:{alt}",
            )
            expanded.append(normalized)
            status = normalized["normalization_status"]
            status_counts[status] = status_counts.get(status, 0) + 1

    # Deduplicate after normalization and sort deterministically.
    unique = {}
    for row in expanded:
        key = (row["chrom"], row["pos"], row["ref"], row["alt"])
        unique[key] = row
    outputs = sorted(
        unique.values(),
        key=lambda row: (
            str(row["chrom"]),
            int(row["pos"]),
            str(row["ref"]),
            str(row["alt"]),
        ),
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "##fileformat=VCFv4.2",
        "##source=WGR-CDP_reference_aware_normalizer",
        f"##reference={reference_build}",
        "##wgr_cdp_normalization_status=reference_aware",
        '##INFO=<ID=WGR_NORM,Number=1,Type=String,Description="WGR-CDP normalization status">',
        '##INFO=<ID=WGR_REF_CHECK,Number=1,Type=String,Description="WGR-CDP reference validation status">',
        '##INFO=<ID=WGR_ORIG,Number=1,Type=String,Description="Original variant before normalization">',
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO",
    ]
    with out.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(headers) + "\n")
        for row in outputs:
            handle.write("\t".join([
                str(row["chrom"]),
                str(row["pos"]),
                "." if row.get("id") in (None, "") else str(row["id"]),
                str(row["ref"]),
                str(row["alt"]),
                "." if row.get("qual") in (None, "") else str(row["qual"]),
                str(row.get("filter") or "PASS"),
                str(row.get("info") or "."),
            ]) + "\n")

    mismatch = status_counts.get("reference_mismatch", 0)
    unavailable = sum(
        count for status, count in status_counts.items()
        if status in {UNAVAILABLE, "normalization_validation_failed"}
    )
    return {
        "schema_version": "A13-NORMALIZATION-1",
        "status": (
            "PASS"
            if outputs and mismatch == 0 and unavailable == 0
            else "FAIL"
            if mismatch > 0
            else "CONDITIONAL"
        ),
        "input_file": str(input_path),
        "output_file": str(out),
        "reference_fasta": str(reference_fasta),
        "reference_build": reference_build,
        "input_record_count": len(records),
        "expanded_record_count": len(expanded),
        "deduplicated_record_count": len(outputs),
        "status_counts": status_counts,
        "reference_fasta_sha256": _sha256(reference_fasta),
        "reference_mismatch_count": mismatch,
        "normalization_required": False,
    }
