"""Data ingestion utilities for WGR-CDP."""

from .vcf import read_vcf
from .normalize import normalize_variant

__all__ = ["read_vcf", "normalize_variant"]
