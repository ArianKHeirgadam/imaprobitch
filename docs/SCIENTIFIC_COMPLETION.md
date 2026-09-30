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