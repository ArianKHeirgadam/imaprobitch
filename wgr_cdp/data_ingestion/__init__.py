"""Data ingestion utilities for WGR-CDP."""

from .vcf import read_vcf
from .normalize import normalize_variant

from .gdc import fetch_project, query_files, build_intake_record, write_intake_record

__all__ = ["read_vcf", "normalize_variant", "fetch_project", "query_files", "build_intake_record", "write_intake_record"]
