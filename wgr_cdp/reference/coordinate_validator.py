"""Coordinate validation layer."""

from .genome_build import resolve_build


def validate_coordinate(chromosome, position, genome_build):
    if resolve_build(genome_build) is None:
        return False

    if not chromosome:
        return False

    if not isinstance(position, int):
        return False

    if position <= 0:
        return False

    return True
