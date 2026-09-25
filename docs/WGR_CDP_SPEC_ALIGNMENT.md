# WGR-CDP Specification Alignment

This document is the authoritative mapping between the repository and the WGR-CDP research specification. The numbered WGR-CDP phases are not interchangeable with the repository's historical implementation phases.

## Current scientific gate

**STOPPED at WGR-CDP Phase 2.** The repository's Phase 2 status records that the test suite was not executed in the available environment. Under the specification, later scientific phases cannot be accepted until this gate is resolved.

## Mapping

| WGR-CDP phase | Required scope | Current state |
|---|---|---|
| 0 | Audit, novelty review, prior-art table | Artifacts present; re-audit after alignment |
| 1 | Dataset manifest/access governance | Manifest exists; datasets not verified/downloaded |
| 2 | GRCh38 harmonization, QC, exclusion audit, tests | Foundational framework exists; execution gate unresolved |
| 3 | Real SNV/Indel, CNV/SV, methylation, mitochondrial extraction | Not implemented as required |
| 4 | Exact genome discovery | Not implemented |
| 5 | WGR-CDP multi-resolution scanner | Not implemented |
| 6 | Exact-vs-WGR-CDP benchmark | Not implemented |
| 7 | Blood background / PoN / CHIP | Not implemented |
| 8 | cfDNA detectability simulation/scoring | Not implemented |
| 9 | Patient-candidate detectability matrix | Not implemented |
| 10 | Early-stage evidence/specificity/differential analysis | Not implemented |
| 11 | Reproducible literature whitespace analysis | Not implemented |
| 12 | Transparent candidate ranking + sensitivity analysis | Not implemented |
| 13 | Greedy/ILP complementary panel optimization | Not implemented |
| 14 | Matched conventional baselines | Not implemented |
| 15+ | Ablation, leakage freeze, validation, reproducibility, paper/audit | Blocked by earlier gates |

## Important correction

The existing files named `PHASE_4_STATUS.md` through `PHASE_14_STATUS.md` describe repository-infrastructure milestones, not WGR-CDP scientific phases 4 through 14. They are retained as historical implementation records and must not be interpreted as scientific completion.

## Data integrity rules

- Never invent accession IDs, sample counts, p-values, effect sizes, AUC, sensitivity, specificity, LoD, validation results, or literature counts.
- Use `Data unavailable` when required evidence is absent.
- `Not detected` is reserved for an actually analyzed sample/feature with a negative result.
- Missing blood-background evidence is not converted into negative evidence.
- Every exclusion records sample ID, reason, module, and timestamp.
- Every scientific hit is traceable to exact-resolution evidence.
- Every phase requires implementation, tests, results, limitations, acceptance checklist, and GO/NO-GO.

## Next work

1. Run the complete test suite in CI.
2. Resolve Phase-2 failures or environment blockers.
3. Re-issue Phase-2 GO/NO-GO from actual execution evidence.
4. Only after Phase 2 is GO, implement WGR-CDP Phase 3 real feature extraction.
5. Do not relabel historical infrastructure phases as scientific completion.
