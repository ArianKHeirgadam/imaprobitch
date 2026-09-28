# Phase 21 — Cohort & Population Analysis

Adds the first case/control cohort-comparison layer to WGR-CDP.

## Added

- Stable case/control cohort normalization.
- Per-sample carrier deduplication.
- Variant-level case/control carrier counts.
- Variant carrier frequencies in each cohort.
- Frequency difference.
- Case/control frequency ratio.
- Dependency-free two-sided Fisher exact test.
- Gene-level carrier comparison from annotated variant records.
- Explicit validation that both case and control cohorts exist.

## Input model

A minimal variant cohort uses:

```python
[
    {
        "sample_id": "C1",
        "group": "case",
        "variants": ["17:7579472:C:T"],
    },
    {
        "sample_id": "H1",
        "group": "control",
        "variants": [],
    },
]
```

Gene comparison additionally accepts `variant_records`:

```python
{
    "sample_id": "C1",
    "group": "case",
    "variants": ["v1"],
    "variant_records": [
        {"gene": "TP53"}
    ],
}
```

## Output

Each compared feature contains:

- case/control carrier counts
- case/control cohort sizes
- case/control carrier frequencies
- frequency difference
- case/control frequency ratio
- two-sided Fisher exact p-value

## Data flow

Healthy cohort + cancer cohort
→ normalized case/control samples
→ carrier counting
→ variant/gene frequency comparison
→ Fisher exact test
→ differential feature table

## Scope

This is a research-oriented cohort comparison layer. It does not:

- correct for multiple testing yet
- adjust for covariates
- perform population stratification
- establish causality
- produce clinical diagnostic decisions

Those concerns remain for later statistical/benchmarking phases.

## Testing

All statistical calculations are dependency-free and deterministic.
