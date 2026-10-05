# WGR-CDP Scientific Completion

This additive layer implements the major methodology gaps identified by the WGR-CDP specification without deleting the existing API/database or analysis components.

Implemented:
- cfDNA detectability, power and LoD
- patient x candidate D[p,c]
- exact and 5Mb -> 1Mb -> 100kb -> 10kb -> 1kb -> base scan framework
- fast-vs-exact benchmark metrics
- explicit blood-background model
- complementary patient-coverage panel optimization
- exact 0/1 optimization fallback for small candidate spaces
- global per-feature FPR correction
- baseline helpers
- discovery/frozen/validation leakage states
- bootstrap stability
- canonical ablation definitions
- literature whitespace evidence records with Data unavailable preservation

Scientific boundary:
These modules do not manufacture biological results. Synthetic tests validate software behavior only. Plasma validation, clinical sensitivity/specificity, AUC, and assay-specific LoD remain Data unavailable unless real validation data are supplied.

The exact 0/1 optimizer is mathematically exact for small candidate sets; large candidate spaces should use a dedicated ILP solver under a locked environment.

## Phase A1 — Multi-Resolution Scientific Scanner

Phase A1 implements the PDF-defined WGR-CDP coarse-to-fine discovery path:

- 5 Mb -> 1 Mb -> 100 kb -> 10 kb -> 1 kb -> base/breakpoint.
- SNV/INDEL screening uses patient recurrence and variant-density evidence.
- CNV uses log2-ratio/segment-mean measurements when available.
- Methylation uses beta/M-value measurements when available.
- Mitochondrial features use heteroplasmy/copy-number measurements when available.
- Each retained region carries an auditable parent-to-child lineage.
- Retained regions expand by configurable +/- k neighboring bins before the next resolution.
- Every retained native feature is independently exact-checked.
- Exact p-values are FDR-adjusted; final significance is reported separately from retention.
- The scanner is deterministic and dependency-light.

Phase A1 acceptance criteria:
1. All six resolutions are represented in the output.
2. Feature-specific statistics are selected from the appropriate measurement model.
3. Tumor/control differences and effect sizes are retained in the discovery lineage.
4. Neighbor expansion is configurable and auditable.
5. Exact validation is independent of coarse screening significance.
6. Final q-values are recalculated over the exact validation set.
7. Existing scientific completion tests remain compatible.

Scientific boundary:
A1 validates the discovery computation and its software behavior. It does not claim
biological significance, clinical utility, diagnostic sensitivity/specificity, or
independent-cohort performance without real data.


## Phase A2 — Exact-vs-WGR-CDP Benchmarking

Phase A2 implements the PDF benchmark requirement without inventing biological
performance:

- exact/native discovery and WGR-CDP receive identical input data;
- TP/FP/FN, recall and precision are calculated from significant-hit overlap;
- runtime and peak memory are measured independently;
- evaluated-region counts are reported;
- breakdown by feature type is available;
- explicit parameter sweeps produce recall-vs-cost records;
- a non-dominated recall/cost frontier is reported;
- poor recall is retained as a measured result rather than hidden.

Acceptance criteria:
1. Exact and WGR-CDP receive the same dataset.
2. TP/FP/FN, recall and precision are explicitly reported.
3. Runtime and peak memory are measured.
4. Feature-type breakdown is available.
5. Parameter sweeps are reproducible from explicit parameters.
6. Recall-vs-cost output exposes the measured frontier.
7. Synthetic tests are not presented as biological validation.


## Phase A4 — cfDNA Detectability

A4 now provides:
- the required tumor-fraction grid: 0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005;
- analytical power and computational LoD;
- region size and informative-site parameters;
- copy number, sequencing depth, assay error and blood-background penalty;
- patient-specific candidate detectability inputs;
- Monte-Carlo simulation for analytical-model validation;
- explicit low-pass SNV/INDEL feasibility metadata rather than assuming reliable detection.

A4 remains a computational research model. No biological performance, clinical LoD, sensitivity, specificity or validation result is claimed without real data.

Acceptance criteria:
1. Analytical detectability is monotonic under controlled assumptions.
2. Analytical power can be compared against simulation.
3. Required tumor fractions are represented exactly.
4. Missing/patient-absent candidates can be represented as zero detectability.
5. Low-pass SNV/INDEL limitations are explicit.
6. No clinical interpretation is inferred from the score.


## Phase A5 — Candidate Evidence, Literature Whitespace, and Sensitivity

A5 adds an auditable candidate-evidence layer after discovery and cfDNA feasibility:

- separate biological, statistical, detectability, blood-background, early-stage, specificity, and literature evidence fields;
- hard assay/FPR/detectability/background constraints are applied before ranking;
- transparent weighted scoring records the fields actually used and preserves Data unavailable;
- Stage I-II versus III-IV evidence can be summarized without inventing missing stage labels;
- healthy and supplied differential comparator groups can be evaluated separately;
- reproducible PubMed query templates and optional live ESearch records store exact query, source, date, result count, and status;
- literature novelty, validation gap, and diagnostic utility remain separate evidence types;
- weight sensitivity scenarios and selection stability are available for audit.

A5 does not claim that a candidate is novel, clinically useful, or globally absent from the literature. Those conclusions require actual literature retrieval and manual review. NCBI documents ESearch as the Entrez text-query interface used by the optional PubMed search layer.

Acceptance criteria:
1. Missing evidence is never silently converted to zero.
2. Hard constraints exclude ineligible candidates before eligible ranking.
3. Weighted scores expose the evidence fields used.
4. Stage and comparator analyses preserve missing-data semantics.
5. Literature records are reproducible and auditable.
6. Sensitivity analysis reports ranking changes across explicit weight scenarios.
7. Existing A1-A4 behavior remains unchanged.

## Phase A6 — Baseline, Ablation, Bootstrap Stability, and Holdout Validation

A6 is implemented as an executable evaluation layer over the actual A5 candidate
universe rather than as a disconnected test-only module.

Implemented components:

- a conventional statistical/effect-size feature-ranking baseline using the same candidate universe;
- identical candidate constraints for baseline and WGR-CDP comparison;
- explicit selection-overlap reporting, deliberately not mislabeled as predictive recall/precision;
- runtime and peak-memory measurements for the baseline and integrated ranking operations;
- complementary patient-coverage optimization for the full WGR-CDP selection when a real patient × candidate matrix is available;
- canonical ablations removing detectability, blood-background, early-stage, specificity, and complementary optimization components;
- explicit single-layer and exact-scan-only comparison records;
- deterministic bootstrap rank/selection stability with configurable seed and iteration count;
- optional independent validation-candidate revalidation;
- missing validation inputs remain `Data unavailable`;
- no clinical sensitivity, specificity, AUC, prospective performance, or independent-cohort result is inferred from synthetic tests.

### A6 acceptance criteria

1. Baseline and WGR-CDP use the same candidate universe.
2. Baseline selection is deterministic under identical input.
3. Baseline/WGR selection overlap is reported without presenting it as predictive performance.
4. Panel coverage is calculated from an actual patient × candidate matrix when supplied.
5. Full WGR-CDP uses complementary optimization when that matrix is available.
6. Ablations explicitly remove named evidence components and report their selection/coverage.
7. Bootstrap stability is reproducible from an explicit seed and iteration count.
8. Independent validation candidates can be supplied separately from discovery candidates.
9. Missing independent validation remains `Data unavailable`.
10. All A1-A5 behavior remains compatible.

### A6 artifacts

An end-to-end CLI run now additionally writes:

- `a6_validation.json`
- `a6_baseline_comparison.json`
- `a6_bootstrap_stability.json`
- `a6_ablation.csv`

Optional independent validation input is supplied with:

`--validation-candidates <csv>`

Bootstrap iterations are controlled with:

`--bootstrap <N>`


## Phase A7 — Final Multimodal Evidence Integration and Panel Design

A7 is the terminal computational panel-design layer. It consumes the complete
auditable A5 candidate universe plus the real patient × candidate detectability
matrix when available.

Implemented:

- multimodal cohort evidence is mapped into the same auditable A5 evidence schema;
- common aliases for detectability, power, blood-background, early-stage,
  specificity, FDR/q-value, and validation fields are accepted;
- missing measurements remain exactly `Data unavailable` and are never converted
  into negative evidence;
- hard assay/FPR/detectability/background constraints are applied before ranking;
- transparent weights are inherited from the canonical A5 weight definition;
- ranking remains visible separately from complementary panel optimization;
- complementary optimization is performed over the full eligible candidate
  universe, not only the first K ranked candidates;
- exact 0/1 optimization is used for small candidate universes and deterministic
  greedy optimization is used when the exact search space is too large;
- the selected panel's patient coverage is computed directly from the supplied
  probability matrix;
- a reproducible per-feature FPR allocation is recorded from the requested
  family-wise target and selected panel size;
- final panel membership is explicitly marked in the complete ranked candidate CSV;
- final constraints/weights are persisted separately for audit;
- the real CLI path writes the final panel and appends a dedicated A7 report section.

A7 artifacts:

- `final_panel.json`
- `final_panel_candidates.csv`
- `final_panel_constraints.json`

### A7 acceptance criteria

1. Multimodal evidence enters the canonical candidate schema.
2. Missing multimodal evidence remains explicitly unavailable.
3. Hard constraints are evaluated before eligible ranking.
4. Ranking and coverage optimization are separate, auditable operations.
5. Optimization considers the full eligible universe.
6. Patient coverage is calculated from an actual patient × candidate matrix when supplied.
7. Exact optimization is used for small candidate universes; a documented greedy fallback is used for larger ones.
8. FPR allocation is explicit and reproducible.
9. Final panel membership is machine-readable and traceable to the ranked evidence table.
10. The end-to-end CLI writes all A7 artifacts and a dedicated report section.
11. No biological, diagnostic, or clinical performance result is invented without real validation data.

The final panel remains a computational research-design output. It does not by
itself establish clinical sensitivity, specificity, AUC, prospective utility,
or assay LoD.


### A7 completion audit addendum

The final-panel layer additionally exposes:
- an explicit K <= 15 cap;
- a configurable marginal-coverage stopping threshold (default 0.02);
- coverage-versus-K and marginal-gain diagnostics;
- greedy-versus-exact optimization comparison where exact optimization is feasible;
- bootstrap panel-selection stability with an explicit seed;
- optional per-layer contribution analysis;
- hard assay/FPR constraints before panel optimization;
- final_panel_diagnostics.json as a machine-readable audit artifact.

Literature search now supports both PubMed and Europe PMC as separate, source-labelled records. Logistic and elastic-net baseline helpers are available when labelled data are actually supplied; without labels they remain Data unavailable.

These additions are additive and do not replace the previously validated A1-A6 APIs.


## C-10 — Literature Evidence Provenance

C-10 completes the literature-whitespace specification without creating a second
evidence/scoring system.

Implemented:
- explicit candidate/feature + gene + region search identity;
- three query intents, each with gastric-cancer and cfDNA/ctDNA/plasma/liquid-biopsy context;
- independent PubMed and Europe PMC retrieval;
- source-separated counts and provenance-bearing records;
- manual review status on every record;
- c10.literature.v1 JSON and CSV artifacts;
- compatibility retention of A5 literature_whitespace.json;
- explicit Data unavailable handling for unperformed or failed searches;
- no automatic novelty, validation-gap, or diagnostic-utility claim from counts.

Scientific boundary:
C-10 does not claim global literature novelty, biological efficacy, clinical
utility, diagnostic performance, or assay validation. Retrieval counts require
manual review before they can support a literature interpretation.


## C-11 — End-to-End Integration Gate

C-11 audits the concrete research CLI execution path rather than treating the
legacy stage-envelope runner as evidence of end-to-end execution.

Implemented:
- required artifact groups across base cohort analysis, A5, A6, A7, A8, C-09 and C-10;
- cross-stage consistency checks for A5 candidate partitioning;
- C-10 schema and JSON/CSV record-count consistency;
- A7 K <= 15 enforcement at the integration boundary;
- explicit A8 quality-gate state validation;
- final report presence check;
- machine-readable c11.integration.v1 manifest and artifact index;
- ordering before A9 so the final reproducibility manifest hashes C-11 outputs.

Scientific boundary:
A C-11 PASS establishes software-level integration and provenance completeness,
not biological significance, clinical performance, assay LoD, independent-cohort
performance, or literature novelty.
