"""Common variant representation layer."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VariantRecord:
    chromosome: str
    position: int
    variant_type: str
    reference: str
    alternate: str
    sample_id: Optional[str] = None
    genome_build: str = "GRCh38"
    vaf: Optional[float] = None


SUPPORTED_VARIANT_TYPES = {
    "SNV",
    "INDEL",
    "SV",
    "CNV",
    "METHYLATION",
}


def validate_variant(record: VariantRecord):
    if record.variant_type not in SUPPORTED_VARIANT_TYPES:
        return False

    if record.position <= 0:
        return False

    if not record.chromosome:
        return False

    return True
