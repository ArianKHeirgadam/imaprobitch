# Phase 19 — dbSNP Integration

Adds a read-only dbSNP integration through NCBI Variation Services.

## Added

- Dependency-free `DbSnpClient`.
- VCF-style coordinate → contextual SPDI resolution.
- SPDI → dbSNP rsID resolution.
- RefSNP lookup for the resolved rsID.
- Stable dbSNP annotation fields.
- Injectable HTTP layer for deterministic tests.
- `dbsnp_adapter` compatible with the existing annotation pipeline.
- Preservation of provider-specific ClinVar/dbSNP identifiers in the annotation mapper.

## Data flow

VCF variant
→ NCBI contextual SPDI
→ dbSNP rsID
→ RefSNP record
→ WGR-CDP annotation

NCBI Variation Services exposes VCF contextualization and SPDI-to-rsID
resolution, while RefSNP records provide the dbSNP record representation.

## Scope

This phase adds dbSNP identity/variant metadata integration. It does not
perform cohort comparison, cancer-vs-control statistics, or diagnostic
classification.

## Testing

All network access is injected in tests; the test suite does not depend on a
live NCBI service.
