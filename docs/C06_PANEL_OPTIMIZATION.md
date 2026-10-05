# C-06 — Panel optimization hardening

## Scope

C-06 hardens the research panel-selection layer. It does not establish clinical optimality or diagnostic performance.

## Selection contract

- Panel size is capped at K <= 15 regardless of caller input.
- Candidate ranking remains separate from panel optimization; optimization may select a lower-ranked complementary candidate when patient coverage improves.
- Exact 0/1 search is used only for bounded candidate universes; larger universes use deterministic greedy selection.
- The optimization method and selected candidates are recorded in the final-panel artifacts.
- FPR target is validated as a finite value in (0, 1]; the per-feature budget is derived from the selected panel size.

## Missingness contract

- A missing candidate observation is not interpreted as a negative/non-detection.
- Coverage denominators include only patients with at least one observed selected feature.
- Explicit numeric zero remains an observed non-detection.
- Invalid/non-finite matrix values are excluded from coverage rather than converted into negative evidence.

## Scientific limits

Panel coverage is a computational prioritization objective over the supplied patient-by-candidate matrix. It is not clinical sensitivity, specificity, PPV, NPV, or proof of diagnostic utility. Missing matrix observations cannot establish absence of a feature.

## Regression coverage

tests/test_panel_optimization.py verifies missingness-aware coverage, explicit-zero semantics, FPR validation, and K capping.