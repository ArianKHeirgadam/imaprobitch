# Phase 16 — Real Data Ingestion Layer

## Added
- Dependency-free VCF reader for standard mandatory VCF columns.
- Basic VCF validation for malformed rows.
- Stable variant normalization representation.
- Unit tests using temporary VCF input.

## Scope
This phase connects the framework to real variant-file input without introducing external annotation databases or machine-learning models.

## Not yet included
- FASTQ/BAM processing
- external annotation database integration
- clinical interpretation
- machine-learning training/inference
