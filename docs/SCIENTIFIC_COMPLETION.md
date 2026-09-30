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
