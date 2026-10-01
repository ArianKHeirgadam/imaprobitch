"""Data ingestion utilities for WGR-CDP."""

from .vcf import read_vcf
from .normalize import normalize_variant

from .gdc import fetch_project, query_files, build_intake_record, write_intake_record

__all__ = ["read_vcf", "normalize_variant", "fetch_project", "query_files", "build_intake_record", "write_intake_record"]

from .gdc_acquisition import (
    inventory_files, classify_file, build_acquisition_manifest,
    write_acquisition_manifest, write_tsv_manifest, verify_file,
    download_file, acquire_manifest, register_dataset, write_registration,
)

from .gdc_cohort import query_cases, query_variant_files, classify_sample, build_cohort_manifest, write_cohort_manifest
