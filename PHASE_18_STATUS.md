# Phase 18 — ClinVar Integration

Adds a read-only ClinVar integration through NCBI E-utilities and connects it to
the Phase 17 annotation adapter boundary.

## Added
- Dependency-free ClinVar client using NCBI E-utilities.
- Coordinate-style variant lookup.
- Stable mapping into the WGR-CDP annotation schema.
- Injectable HTTP layer for deterministic tests.
- ClinVar adapter compatible with `annotate_variants`.
- Tests for successful lookup, missing variants, and pipeline integration.

## Design
The network client is isolated behind `request_get`, so the test suite does not
depend on internet access or live ClinVar responses.

## Scope
This phase performs read-only annotation lookup. It does not make diagnostic
decisions or replace professional clinical interpretation.
