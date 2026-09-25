"""Variant annotation and feature extraction layer."""

from dataclasses import dataclass, asdict


@dataclass
class VariantFeature:
    chromosome: str
    position: int
    variant_type: str
    vaf: float | None = None
    impact: str | None = None
    functional_class: str | None = None
    recurrence: int = 0


def annotate_variant(record):
    """
    Convert a VariantRecord into a feature representation.
    This phase does not perform external database annotation.
    """
    return VariantFeature(
        chromosome=record.chromosome,
        position=record.position,
        variant_type=record.variant_type,
        vaf=record.vaf,
    )


def feature_dict(feature):
    return asdict(feature)
