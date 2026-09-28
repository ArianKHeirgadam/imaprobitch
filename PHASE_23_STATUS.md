# Phase 23 — Statistical & Benchmarking

Adds statistical safeguards and evaluation utilities on top of the existing
cohort comparison layer.

## Added

- Benjamini-Hochberg false-discovery-rate correction.
- Stable q-values returned in original input order.
- FDR/significance filtering.
- Dependency-free binary benchmark summary.
- Accuracy, precision, recall, and specificity.
- Validation of p-value and alpha ranges.
- Input rows are not mutated by FDR processing.

## Data flow

Cohort comparison
→ raw p-values
→ Benjamini-Hochberg q-values
→ significance filtering
→ candidate/evidence prioritization

A separate benchmark helper provides standard binary prediction metrics when
a reference label and prediction vector are available.

## Important scope

This phase does not claim clinical validity, diagnostic performance, or
biomarker status. FDR correction is a statistical safeguard; it does not
solve population stratification, batch effects, confounding, or causal
inference.

The benchmark helper reports metrics for supplied labels/predictions. It does
not train a machine-learning model.
