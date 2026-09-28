# Phase 25 — Final Validation, Documentation & Release

Phase 25 closes the current implementation roadmap with explicit release
metadata, deterministic health checks, and a machine-readable release report.

## Release identity

- Name: WGR-CDP
- Release: 1.0.0
- Status: research
- Clinical diagnostic: false

## Declared capabilities

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

## Final validation

The complete repository test suite remains the authoritative regression check.
The release health check verifies that the declared release metadata contains
the required research components and explicitly states that the framework is
not a clinical diagnostic.

## Release boundary

This release does not claim clinical diagnosis, clinical validation, causal
inference, or clinical utility. Candidate scores are research prioritization
signals only.

## Completion

This phase completes the planned 0–25 implementation roadmap. Future work can
extend the framework with larger real cohorts, covariate-aware models,
population stratification, batch-effect handling, external replication cohorts,
and prospective validation.
