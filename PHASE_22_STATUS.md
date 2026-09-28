# Phase 22 — Candidate / Biomarker Discovery

Adds a transparent candidate-discovery layer on top of Phase 21 cohort
statistics and the external evidence layers.

## Added

- Candidate evidence aggregation.
- ClinVar evidence flag.
- dbSNP evidence flag.
- Functional/VEP evidence flag.
- Bounded 0–100 evidence prioritization score.
- Deterministic candidate ranking.
- Preservation of cohort statistics and external evidence in the candidate.
- Stable handling of missing annotation evidence.

## Evidence model

Candidate prioritization uses:

1. Absolute case/control frequency difference.
2. Fisher exact p-value thresholds.
3. ClinVar identifier/accession presence.
4. dbSNP identifier presence.
5. Functional evidence for a gene.
6. Functional consequence presence.

The score is deliberately transparent and bounded. It is a research
prioritization score, not a probability, clinical score, diagnostic result, or
proof of biomarker status.

## Data flow

Case/control results
→ annotation evidence
→ functional evidence
→ evidence flags
→ transparent evidence score
→ deterministic candidate ranking

## Scope

This phase does not establish a biomarker, causality, clinical validity, or
clinical utility. Multiple-testing correction and covariate-aware statistical
models remain future work.
