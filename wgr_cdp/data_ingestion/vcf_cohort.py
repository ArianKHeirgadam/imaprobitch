"""VCF cohort ingestion with multi-allelic and multi-sample support."""

import gzip
from pathlib import Path


def _open_text(path):
    path = Path(path)
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open("r", encoding="utf-8")


def _variant_type(ref, alt):
    if len(ref) == 1 and len(alt) == 1:
        return "SNV"
    return "INDEL" if len(ref) != len(alt) else "MNV"


def _has_alt(genotype):
    if not genotype:
        return True
    gt = str(genotype).split(":", 1)[0]
    if gt in {".", "./.", ".|."}:
        return False
    alleles = gt.replace("|", "/").split("/")
    return any(a.isdigit() and int(a) > 0 for a in alleles)


def read_vcf_cohort(path, group, sample_prefix=None):
    """Return sample dictionaries from either single- or multi-sample VCF.

    Multi-allelic ALT fields are decomposed into independent biallelic records.
    If FORMAT/GT columns are present, a variant is assigned to a sample only
    when that sample carries an alternate allele. For a simple 8-column VCF,
    each file is treated as one sample and every record is a carrier.
    """
    path = Path(path)
    if not path.exists():
        raise ValueError(f"VCF does not exist: {path}")
    sample_names = []
    records_by_sample = {}
    with _open_text(path) as handle:
        raw_text = handle.read()
    raw_text = raw_text.replace(chr(92) + "n", chr(10)).replace(chr(92) + "t", chr(9))
    for line_number, raw in enumerate(raw_text.splitlines(), start=1):
            line = raw.rstrip("\r\n")
            if not line:
                continue
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                fields = line.split("\t")
                sample_names = fields[9:]
                for name in sample_names:
                    records_by_sample[name] = []
                continue
            if line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) < 8:
                raise ValueError(f"Invalid VCF row at line {line_number}: expected at least 8 columns")
            chrom, pos, ident, ref, alt_field, qual, filt, info = fields[:8]
            try:
                pos = int(pos)
            except ValueError as exc:
                raise ValueError(f"Invalid VCF position at line {line_number}: {fields[1]}") from exc
            alts = alt_field.split(",")
            format_keys = fields[8].split(":") if len(fields) >= 9 else []
            genotype_values = fields[9:] if len(fields) >= 10 else []

            def make_record(alt, sample_name=None, sample_value=None):
                info_map = {}
                for item in info.split(";"):
                    if "=" in item:
                        k, v = item.split("=", 1)
                        info_map[k.upper()] = v
                return {
                    "chrom": chrom,
                    "pos": pos,
                    "id": None if ident == "." else ident,
                    "ref": ref,
                    "alt": alt,
                    "qual": None if qual == "." else qual,
                    "filter": filt,
                    "info": info,
                    "variant_key": f"{chrom}:{pos}:{ref}:{alt}",
                    "variant_type": _variant_type(ref, alt),
                    "gene": info_map.get("GENE") or info_map.get("GENE_SYMBOL") or info_map.get("SYMBOL"),
                    "consequence": info_map.get("CONSEQUENCE") or info_map.get("CSQ_CONSEQUENCE"),
                    "impact": info_map.get("IMPACT") or info_map.get("CSQ_IMPACT"),
                    "sample_genotype": sample_value,
                }

            if sample_names:
                for index, sample_name in enumerate(sample_names):
                    sample_value = genotype_values[index] if index < len(genotype_values) else ""
                    gt = sample_value.split(":", 1)[0]
                    allele_numbers = {int(a) for a in gt.replace("|", "/").split("/") if a.isdigit()}
                    for alt_index, alt in enumerate(alts, start=1):
                        if alt_index in allele_numbers:
                            records_by_sample[sample_name].append(make_record(alt, sample_name, sample_value))
            else:
                fallback = sample_prefix or path.stem.replace(".vcf", "")
                records_by_sample.setdefault(fallback, [])
                for alt in alts:
                    records_by_sample[fallback].append(make_record(alt, fallback, None))

    samples = []
    for sample_name, records in records_by_sample.items():
        unique = {r["variant_key"]: r for r in records}
        samples.append({
            "sample_id": sample_name,
            "group": group,
            "variants": sorted(unique),
            "variant_records": list(unique.values()),
            "source_file": str(path),
        })
    return samples
