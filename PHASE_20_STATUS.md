# Phase 20 — Biological / Functional Evidence Layer

Adds a provider-neutral functional evidence layer backed by Ensembl Variant
Effect Predictor (VEP).

## Added

- Dependency-free `VepClient`.
- Injectable HTTP layer for deterministic tests.
- Transcript consequence extraction.
- Gene and transcript identifiers.
- Protein-change field when supplied by VEP.
- Regulatory consequence extraction.
- Stable functional evidence schema.
- `vep_adapter` compatible with the new evidence pipeline.
- Non-mutating `add_functional_evidence` pipeline.

## Data flow

Normalized variant
→ Ensembl VEP
→ transcript/protein/regulatory consequences
→ normalized functional evidence
→ downstream feature fusion / candidate analysis

VEP can report affected genes/transcripts, sequence consequences, regulatory
features and additional prediction/annotation fields. This phase intentionally
keeps the first integration narrow and stable rather than importing every VEP
field.

## Scope

This phase describes biological/functional consequences of variants. It does
not compare healthy and cancer cohorts, establish causality, or make clinical
diagnoses.

## Testing

All network access is injected in tests. The test suite does not depend on a
live Ensembl service.
