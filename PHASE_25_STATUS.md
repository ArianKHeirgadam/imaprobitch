# Phase 25 — Final Validation, Documentation & Release

Phase 25 is retained as the historical release milestone for the original 0–25 roadmap. Release 1.1.0 supersedes the original 1.0.0 identity after the A8/A9 completion track.

## Current release identity

- Name: WGR-CDP
- Release: 1.3.0
- Status: research
- Clinical diagnostic: false

## Current declared capabilities

- VCF ingestion
- QC and normalization
- Annotation / feature fusion
- ClinVar integration
- dbSNP integration
- Ensembl VEP functional evidence
- Case/control cohort comparison
- Fisher exact testing
- Benjamini-Hochberg FDR correction
- Candidate evidence prioritization
- Pipeline hardening
- Run tracking and validation

## Release validation

The complete repository test suite remains the authoritative regression check.
The release health check verifies declared research components. A9 additionally records run provenance and artifact checksums.

## Release boundary

This release does not claim clinical diagnosis, clinical validation, causal
inference, or clinical utility. Candidate scores are research prioritization
signals only.

## A9 provenance

Completed runs write `reproducibility_manifest.json` with run ID, configuration, Python/platform information and SHA-256 hashes of generated artifacts.

## Scientific boundary

Software tests establish implementation behavior, not biological validity. The project remains research-only and scientific conclusions remain conditional on real data and independent validation.
