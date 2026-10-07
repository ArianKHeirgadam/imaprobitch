# A15 — CNV Detection / Validation

## Status

IMPLEMENTATION COMPLETE — pending real-data validation

## Implemented
- GDC-style CNV segment ingestion support
- GAIN/LOSS/NEUTRAL classification
- separate event-level carrier statistics
- Fisher exact testing
- event effect size and BH-FDR
- separate continuous dosage statistics
- reproducible permutation testing
- dosage effect size and BH-FDR
- explicit case/comparator denominators
- missingness semantics
- SHA-256 input provenance
- CLI validation command with optional sample-group metadata mapping
- regression tests

## Real-data status

No biological result is fabricated. Real TCGA CNV execution remains pending local data validation. Independent healthy CNV inference remains Data unavailable unless an independent healthy cohort is explicitly supplied.

## Closure requirements
- full authoritative test suite
- real TCGA CNV validation
- event/dosage denominator audit
- provenance audit
- scientific audit
- README/status update