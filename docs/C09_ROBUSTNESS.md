# C-09 — Robustness and Sensitivity Analysis

C-09 is the research-engineering robustness layer for WGR-CDP. It stress-tests
ranking and panel behavior under transparent computational perturbations without
changing the scientific source data.

## Scope

The phase covers four independent axes:

1. **Weight sensitivity** — candidate ranking is recomputed under explicit,
   one-factor weight perturbations around the configured normalized weights.
2. **Threshold sensitivity** — hard detectability and blood-background constraints
   are varied before weighted ranking.
3. **K sensitivity** — deterministic panel selection is evaluated over K values
   with the existing K <= 15 boundary and observation-aware coverage.
4. **Missingness stress** — observed evidence fields are synthetically masked at
   fixed rates using a deterministic seed; this tests software robustness only.

## Contracts

- Weight values must be finite and non-negative; at least one must be positive.
- Weight keys must belong to the canonical evidence schema; unknown components are rejected.
- Thresholds are finite values in [0, 1].
- Panel K is capped at 15.
- Missing observations are never converted to explicit zero.
- `Data unavailable` is preserved and is never interpreted as negative evidence.
- K sensitivity uses the existing observation-aware `panel_coverage` function.
- Missingness stress never mutates caller-owned input rows.
- All perturbation outputs include deterministic seed/repetition metadata where
  applicable.
- C-09 results are descriptive stress tests, not clinical performance results.

## Artifacts

A complete run writes:

- `c09_robustness.json`
- `c09_weight_sensitivity.csv`
- `c09_threshold_sensitivity.csv`
- `c09_k_sensitivity.csv`
- `c09_missingness_stress.csv`

The JSON artifact uses schema `c09.robustness.v1`.

## Interpretation

High ranking stability means that the **software-selected ordering** is stable
under the tested perturbations. Low stability identifies candidates or settings
that are configuration-sensitive and should be treated cautiously.

High K-panel overlap/coverage stability is descriptive of the supplied matrix.
It is not evidence of clinical optimality.

Synthetic missingness is an explicit robustness experiment. It must not be
reported as a biological missingness rate or as evidence about the assay.

## Scientific boundary

C-09 does not establish clinical sensitivity/specificity, AUC, assay-validated
LoD, biological causality, independent-cohort performance, or diagnostic utility.
Those require appropriate real data and validation outside the stress-test layer.

## Acceptance checklist

- Weight validation is strict and deterministic.
- Weight, threshold, K, and missingness analyses are integrated.
- Missing-data semantics are preserved.
- K <= 15 is enforced.
- Artifacts are machine-readable and traceable.
- Tests cover deterministic behavior, invalid inputs, missingness safety, and
  artifact creation.
