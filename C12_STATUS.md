# C-12 Status — Final Scientific Hardening

## Phase status
Implementation: COMPLETE
Local regression: PASS — 378 passed in 3.22s
Phase status: CLOSED
Scientific claims: CONDITIONAL / data-dependent

| Requirement | Implementation | Artifact / API | State |
|---|---|---|---|
| cfDNA suitability | liquid-biopsy suitability component model | c12_candidate_prioritization.json | COMPLETE |
| Recurrence / prevalence | observed case prevalence | candidate_evidence.csv | COMPLETE |
| Patient-level coverage | explicit presence matrix | patient_candidate_presence_matrix.csv | COMPLETE |
| Panel-level optimization | presence-based exact/greedy | final_panel.json | COMPLETE |
| Effect size + p/FDR | SNV/INDEL + CNV event/dosage contracts | cohort/CNV outputs | COMPLETE |
| Formal score | normalized weighted mean over observed components | candidate_evidence.csv | COMPLETE |
| Sensitivity | explicit weight scenarios | ranking_sensitivity.json | COMPLETE |
| Independent validation | frozen-panel coverage | c12_validation_coverage.json | COMPLETE |
| Cohort metadata | platform/batch/confounder audit | c12_cohort_design.json | COMPLETE |
| Evidence hierarchy | typed external evidence | c12_evidence_hierarchy.json | COMPLETE |
| Confidence | evidence-strength semantics | c12_confidence.csv | COMPLETE |
| Final audit | terminal cross-contract gate | c12_final_audit.json | COMPLETE |

## Scientific limitations
- No wet-lab cfDNA detection claim is made.
- Missing assay inputs remain Data unavailable.
- Cohort-design review depends on metadata actually being supplied.
- Literature novelty/validation-gap/diagnostic-utility still require manual review.
- Independent validation remains data-dependent.

## GO / NO-GO
GO for implementation.
CLOSED after the authoritative local full-suite regression passed: `378 passed in 3.22s`.

This closes the C-12 software/scientific hardening phase; data-dependent scientific limitations remain unchanged.
