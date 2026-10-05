# C-07 — Baseline models hardening

## Scope

C-07 completes the baseline-model layer already introduced by A6. It provides dependency-light Logistic and Elastic-Net baselines for labelled research inputs while preserving the framework's missing-data and scientific-integrity contracts.

## Baseline contract

- Baselines use the supplied candidate universe and labels; they do not manufacture labels.
- Logistic and Elastic-Net models return `Data unavailable` when labels are absent, malformed, or single-class.
- Binary labels are restricted to 0/1.
- Non-finite or invalid model parameters do not silently fall back to arbitrary values.
- Panel/feature selection is capped at K <= 15.
- Missing or non-finite numeric features are not interpreted as zero.
- Feature imputation, when needed, uses the median of observed values in the supplied training rows only.
- Features with no observed numeric training value are excluded.
- Deterministic ordering is retained for coefficient-based feature selection.

## Scientific limits

These are computational baselines for comparison and ablation. A fitted baseline is not evidence of clinical performance. Predictive metrics require labelled, patient-level, leakage-safe validation data and remain `Data unavailable` when such data are absent.

## Regression coverage

`tests/test_a6_validation.py` verifies executable labelled baselines, unavailable-without-label semantics, missing-feature handling, invalid/single-class labels, and parameter validation.