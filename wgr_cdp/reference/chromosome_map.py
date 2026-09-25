"""Chromosome normalization utilities."""

CHROMOSOME_MAP = {
    "chr1": "1",
    "chr2": "2",
    "chrX": "X",
    "chrY": "Y",
    "chrM": "MT",
    "chrMT": "MT",
}


def normalize_chromosome(chromosome):
    return CHROMOSOME_MAP.get(
        chromosome,
        chromosome[3:] if chromosome.startswith("chr") else chromosome,
    )
