# A8 — Final Empirical Validation & Reproducibility Gate

A8 is the final empirical-validation layer after A0–A7. It is additive and does
not replace or mutate the working discovery, cfDNA, evidence, benchmark, or
panel-design APIs.

## Scope

A8 checks:

- discovery/validation sample or patient overlap;
- explicit DISCOVERY -> FROZEN -> VALIDATION state transition;
- revalidation of the A7-selected candidate set against an independent table;
- effect-direction concordance where effect measurements are actually supplied;
- bootstrap stability of validation revalidation;
- a transparent final quality gate.

Candidate overlap between discovery and validation is not treated as sample
leakage: the same biological candidate can legitimately be tested in an
independent cohort. Sample/patient overlap is the leakage criterion.

## Status semantics

- PASS: independent validation inputs are present, no sample leakage is
  detected, and the supplied validation checks are executable.
- CONDITIONAL: required empirical validation data are missing.
- FAIL: sample/patient leakage or a reproducibility-state failure is detected.
- Data unavailable: an individual measurement cannot be computed from the
  supplied inputs.

A PASS is a software/data-quality gate. It is not a claim of clinical
sensitivity, specificity, AUC, diagnostic utility, prospective validity, or
assay-validated LoD.

## Inputs

A8 accepts optional:

- discovery candidate rows;
- independent validation candidate rows;
- discovery sample/patient IDs;
- validation sample/patient IDs;
- A7 selected candidate IDs.

If sample IDs are absent, the leakage audit explicitly reports
Data unavailable rather than assuming independence.

## Artifacts

write_a8_artifacts() writes:

- a8_validation.json
- a8_leakage_audit.json
- a8_bootstrap_stability.json
- a8_generalization.json
- a8_generalization.csv
- a8_quality_gate.json

The existing A0–A7 artifacts are left untouched.

## Scientific boundary

Synthetic tests demonstrate implementation behavior only. Real independent
cohort data, verified metadata and external validation remain necessary before
making empirical biological or clinical claims.
