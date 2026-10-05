# C-08 — Ablation and Component Contribution

## Scope

C-08 completes the ablation/contribution layer around the existing A6 ranking and A7 panel optimization. The purpose is to quantify descriptive changes caused by removing framework components while keeping the candidate universe and constraints explicit.

## Canonical ablations

The existing eight ablations are preserved:

- full WGR-CDP
- without detectability
- without complementary optimization
- without blood-background safety
- without early-stage evidence
- without specificity
- single-layer statistical ranking
- exact-scan-only comparison

No new biological evidence is inferred from an ablation.

## Comparison contract

`wgr_cdp.research.ablation.compare()` produces a normalized audit record and, when coverage is actually available, a descriptive `coverage_delta_vs_full`.

`Data unavailable` remains unchanged when the patient × candidate matrix is unavailable. It is never converted to zero.

Selection overlap and coverage deltas are descriptive engineering/research diagnostics; they are not predictive performance, causal effects, clinical utility, or biological significance.

## Layer contribution

`layer_contribution()` uses a leave-one-layer-out coverage calculation. A layer's marginal contribution is:

`coverage(all selected) - coverage(selected without that layer)`

This is a descriptive marginal measure. Contributions are not assumed to be additive when layers overlap in patient coverage.

Missing layer metadata returns `Data unavailable`.

## Reproducibility and safety

- Panel size is capped at K <= 15.
- Bootstrap with a non-positive iteration count returns `Data unavailable`.
- Bootstrap selection remains seed-controlled.
- Missing candidate observations remain missing rather than becoming explicit non-detection.
- No clinical metric is generated without valid labelled patient-level data.

## Tests

Regression tests cover comparison deltas, unavailable coverage, K capping, zero-bootstrap handling, layer metadata safety, and end-to-end A6 integration.
