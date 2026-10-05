# C-12 — Final Scientific Hardening and Release Audit

C-12 is the terminal scientific-hardening phase. It closes the remaining
methodological gaps identified in the WGR-CDP design review without changing
the core VCF -> Cancer/Healthy -> candidate discovery architecture.

## Sub-phases

### C-12.1 — cfDNA-oriented prioritization
- explicit cfDNA suitability schema;
- recurrence/prevalence;
- optional clonality/CCF;
- optional allele fraction/VAF;
- optional unique-mappability;
- optional prior cfDNA evidence;
- optional alteration-type support;
- modeled detectability;
- missingness-aware weighted suitability score.

### C-12.2 — patient-level presence and panel coverage
- explicit patient x candidate presence/absence matrix;
- separate presence matrix from probabilistic detectability matrix;
- individual and panel-level coverage;
- greedy and exact presence-based panel selection;
- K <= 15 and marginal-gain stopping.

### C-12.3 — statistical framework hardening
- SNV/INDEL carrier comparison retains Fisher exact testing;
- CNV event presence remains categorical Fisher testing;
- continuous CNV dosage receives a reproducible permutation test;
- dosage effect size and FDR-adjusted dosage p-values are retained;
- statistical method is explicit in output.

### C-12.4 — cohort design, batch and confounder audit
- explicit metadata contract for platform, instrument, coverage, pipeline,
  reference build, population, batch, library preparation and source;
- optional --cohort-metadata CSV input;
- group-wise metadata balance audit;
- potential confounding is surfaced as REVIEW, not silently ignored.

### C-12.5 — external evidence hierarchy and frozen validation coverage
- typed hierarchy for VEP/Ensembl, dbSNP, ClinVar, cancer-specific evidence,
  and cfDNA-specific evidence;
- same frozen panel can be evaluated on an independent patient-presence matrix;
- validation coverage and coverage delta are retained;
- no validation-cohort re-optimization.

### C-12.6 — evidence-strength confidence
- formal HIGH / MODERATE / LOW / Data unavailable confidence;
- explicit machine-readable thresholds;
- confidence is based on observed computational evidence and score stability;
- confidence is never disease probability.

### C-12.7 — final audit
- C-12 artifact contract;
- score formula and normalized-weight audit;
- evidence-hierarchy audit;
- confidence contract;
- frozen validation contract;
- cohort-design contract;
- patient-presence matrix contract;
- final c12_final_audit.json artifact.

## Acceptance
C-12 closes only when the authoritative local full test suite passes.

A passing C-12 software audit does not establish biological significance,
clinical performance, assay-validated LoD, or independent-cohort validity.
