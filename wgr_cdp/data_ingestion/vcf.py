"""Minimal dependency-free VCF reader for WGR-CDP."""


def read_vcf(path):
    """Read a VCF file into a list of normalized record dictionaries.

    Header lines beginning with ``#`` are ignored. The parser validates that
    each data row has at least the eight mandatory VCF columns.
    """
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.rstrip("\n\r")
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) < 8:
                raise ValueError(f"Invalid VCF row at line {line_number}: expected at least 8 columns")
            records.append({
                "chrom": fields[0],
                "pos": int(fields[1]),
                "id": None if fields[2] == "." else fields[2],
                "ref": fields[3],
                "alt": fields[4].split(","),
                "qual": None if fields[5] == "." else fields[5],
                "filter": fields[6],
                "info": fields[7],
            })
    return records
