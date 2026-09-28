"""Integration layer between ingested variants and annotation adapters."""

from .mapper import map_annotation
from .pipeline import annotate_variants

__all__ = ["map_annotation", "annotate_variants"]
