# C-05 — Candidate ranking and multimodal scoring hardening

## Scope

C-05 hardens the existing candidate evidence/scoring implementation; it does not introduce a new biological model or claim clinical validity.

## Scoring contract

- Evidence values must be finite numeric values. Missing, non-numeric, boolean, NaN, and infinite values are unavailable rather than converted into evidence.
- Available evidence scores are bounded to [0, 1].
- Weighted scores use only available fields with strictly positive weights. The denominator is the sum of weights for those available fields, so missing fields are not treated as zero.
- Weights must be finite and non-negative. Invalid weights raise a `ValueError` instead of silently changing the score.
- The output records which evidence fields contributed to the score and how many were available.

## Eligibility and result buckets

- Hard constraints are evaluated before ranking.
- String booleans such as `"false"`, `"0"`, and `"no"` are parsed as false rather than Python-truthy strings.
- Detectability thresholds are evaluated against observed detectability. An unavailable value cannot satisfy a positive minimum threshold.
- `blood_background_safety` is a safety score (higher is safer); the existing `max_background` configuration is translated to the corresponding minimum safety score.
- Ranked, ineligible, and eligible-but-unscored candidates are disjoint buckets. Their counts sum to the input candidate count.
- Duplicate candidate IDs are reported in an audit block rather than silently deduplicated. They require upstream identity review; the ranker does not fabricate an aggregation rule.

## Scientific limits

A weighted research score is a prioritization heuristic, not a probability of cancer, clinical performance metric, or proof of biological function. Missing literature or assay evidence remains unavailable. Synthetic unit tests verify software contracts only and are not biological validation.

## Regression coverage

`tests/test_a5_candidate_evidence.py` covers missing evidence, hard constraints, transparent weighting, invalid weights, non-finite values, string booleans, mutually exclusive output buckets, and duplicate-ID auditing.
