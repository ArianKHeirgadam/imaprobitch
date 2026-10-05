# PHASE A13 STATUS

## Current state

**OPEN — implementation complete for reference-aware normalization; local verification pending.**

### Verified before normalization
- Study selection: 443 paired TCGA-STAD cases.
- Primary WGS SNV/INDEL files: 430.
- Open WXS MAF fallback files: 434.
- Open-access acquisition smoke test: 2 files verified.
- MAF batch conversion: PASS.
- MAF input files converted: 2.
- Samples converted: 2.
- Variant records converted: 128.
- Structural QC invalid records: 0.
- Structural QC missing provenance tags: 0.
- Test suite immediately before normalization work: 400 passed.

### Implemented in A13 normalization
- Reference-aware REF validation.
- GRCh38 explicit runtime reference.
- Minimal trimming of common bases.
- Repeat-aware left alignment for simple indels.
- Multiallelic expansion.
- Post-normalization deduplication.
- Normalization and reference-check INFO provenance.
- Reference FASTA SHA-256 audit field.
- Single-file and batch normalization CLI.
- Regression tests and CLI parser contracts.

### Scientific gate

A13 is **not CLOSED** until the user runs the full test suite after these
changes and successfully executes normalization against a real GRCh38 reference.

The adapter VCFs remain MAF-derived rather than raw WGS calls. No biological
candidate result is considered validated from the current two-file smoke test.
