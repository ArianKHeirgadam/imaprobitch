"""Variant normalization helpers."""


def normalize_variant(record):
    """Return a stable representation for one VCF variant record."""
    required = ("chrom", "pos", "ref", "alt")
    missing = [key for key in required if key not in record]
    if missing:
        raise ValueError(f"Missing variant fields: {', '.join(missing)}")
    return {
        "chrom": str(record["chrom"]),
        "pos": int(record["pos"]),
        "ref": str(record["ref"]).upper(),
        "alt": [str(allele).upper() for allele in record["alt"]],
    }
