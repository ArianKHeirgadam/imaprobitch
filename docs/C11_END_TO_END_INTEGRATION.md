# C-11 — End-to-End Integration Gate

C-11 is the software-level integration phase for the completed WGR-CDP research
pipeline. It audits the actual CLI research execution path and verifies that
outputs from the core cohort analysis, A5 evidence layer, A6 validation/baselines,
A7 panel design, A8 validation gate, C-09 robustness, and C-10 literature
provenance are present and cross-consistent.

## What C-11 closes

The project has a legacy execute_pipeline runner whose default stages return
validated stage envelopes. That runner remains backward compatible. It is not
treated as evidence that the real research workflow executed.

C-11 therefore audits the concrete run_command path, which performs the real
cohort analysis and then consumes its outputs through A5 -> A7/A6/A8/C-09/C-10,
followed by C-11 and the final A9 reproducibility hash pass.

## Required integration contract

The following artifact groups must exist and be non-empty:

- base cohort analysis and report
- A5 candidate evidence and literature artifacts
- A6 validation, baseline, bootstrap, and ablation artifacts
- A7 final panel and diagnostics artifacts
- A8 validation and quality-gate artifacts
- C-09 robustness artifacts

C-10 is mandatory in the run contract even when live literature searching is
disabled: the resulting records must explicitly retain their not-searched /
Data unavailable state.

## Cross-stage checks

C-11 checks:

1. A5 partition consistency: candidate CSV rows equal ranked + ineligible +
   unscored counts from candidate_constraints.json.
2. C-10 source-separated contract: JSON schema is c10.literature.v1 and JSON
   record count equals the CSV record count.
3. A7 panel cap: selected K never exceeds 15 or the configured effective K.
4. C-09 schema is c09.robustness.v1.
5. A8 quality-gate status is explicit (PASS, CONDITIONAL, or FAIL).
6. The final HTML report remains present after phase sections are appended.

A missing required software artifact is an integration failure. This is distinct
from a missing biological measurement, which remains Data unavailable.

## Artifacts

C-11 writes:

- c11_integration_manifest.json
- c11_artifact_index.csv

The JSON schema is c11.integration.v1.

The manifest contains:

- run ID and configuration snapshot;
- execution contract;
- dependency graph;
- observed optional inputs;
- artifact and cross-stage audit results;
- scientific boundary.

The manifest is intentionally written before A9, so the A9
reproducibility_manifest.json hashes the C-11 artifacts as part of the same run.

## Scientific boundary

C-11 establishes software integration and provenance completeness only. A PASS
does not establish biological significance, clinical sensitivity/specificity,
assay-validated LoD, independent-cohort performance, literature novelty, or
diagnostic utility.

## Acceptance checklist

- [x] Concrete research CLI path is identified as the authoritative execution path.
- [x] Required artifacts from all completed upstream layers are audited.
- [x] Cross-stage count/schema constraints are validated.
- [x] K <= 15 is enforced at the integration boundary.
- [x] A8 conditional validation states are preserved.
- [x] C-11 artifacts are included in the subsequent A9 SHA-256 manifest.
- [x] Synthetic tests cover complete, missing-artifact, and contract-mismatch cases.

## GO / NO-GO

GO for implementation when the test suite passes and a representative real CLI
run produces a C-11 PASS manifest.

NO-GO when a mandatory artifact or cross-stage contract fails. A C-11
implementation PASS still does not become a biological-validation claim.
