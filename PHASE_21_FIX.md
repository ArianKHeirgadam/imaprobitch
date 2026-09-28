# Phase 21 Fix — Preserve Annotated Variant Records

## Bug

`normalize_cohort()` discarded the optional `variant_records` field.

As a result, `compare_gene_cohorts()` received normalized samples without gene
annotations and returned an empty result.

## Fix

- Preserve `variant_records` when present.
- Add a regression test proving that normalization preserves annotated records.
- Keep the existing variant deduplication behavior unchanged.

## Expected result

The Phase 21 suite should increase from:

`46 passed, 1 failed`

to:

`48 passed`
