# C-04 — Leakage-Safe Validation & Evaluation

C-04 hardens the existing A6/A8 validation layer around a strict patient-level evaluation contract.

## Implemented

- deterministic patient-level discovery/validation/test splitting;
- optional patient-level binary-label stratification;
- explicit three-way leakage audit;
- auditable c04.split-manifest.v1 JSON manifests;
- missing/unknown labels remain unavailable and are never converted to negative;
- patient-level binary metrics: sensitivity, specificity, precision, recall, F1, ROC-AUC and PR-AUC when mathematically computable;
- duplicate patient predictions are rejected rather than double-counted;
- threshold fitting is restricted to discovery data;
- validation/test evaluation uses the frozen discovery threshold;
- cross-partition patient overlap is a hard FAIL.

## Data semantics

unknown, missing, unavailable and unrecognized labels are excluded from metric denominators. A metric is null or the evaluation status is Data unavailable when its required class/measurement is absent.

No biological or clinical performance is inferred from software tests or synthetic fixtures.

## Reproducibility

Every split records the seed, requested fractions, partition membership, partition counts, stratification status and leakage audit. The manifest can be persisted with write_split_manifest().

## Scientific boundary

C-04 is a research validation/evaluation layer. A passing software gate does not establish clinical sensitivity, specificity, AUC, diagnostic utility, prospective validity or assay-validated LoD.
