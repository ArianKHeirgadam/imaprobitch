# WGR-CDP Final Scientific & Reproducibility Audit — A0 to A11

## Scope

This audit compares the implemented research framework against the supplied WGR-CDP specification and its stated scientific boundary. The project remains a computational candidate-discovery and panel-design framework, not a clinical diagnostic system.

## A0–A2: discovery and benchmark

- Repository/data-governance infrastructure exists.
- Exact discovery and multi-resolution discovery are implemented.
- Resolutions are 5 Mb, 1 Mb, 100 kb, 10 kb, 1 kb, and base/breakpoint.
- Final coarse-to-fine hits are exact-checked.
- Benchmarking reports recall/precision, runtime, peak memory, evaluated regions, feature-type breakdown and parameter sweeps.
- Measured poor recall is not silently converted into success.

Status: implemented; biological performance remains data-dependent.

## A3: blood background

WBC, healthy-plasma, PoN, gnomAD and CHIP/background fields are represented independently. Missing sources remain Data unavailable and are not treated as negative evidence.

Status: implemented; real background data are required for biological conclusions.

## A4: cfDNA detectability

The required tumor-fraction grid (0.5 through 0.005), sequencing depth, region size, informative sites, copy number, assay error and blood-background penalty are represented. Analytical detectability is compared with Monte-Carlo simulation. Low-pass SNV/INDEL limitations are explicitly marked.

Status: implemented as a computational research model; assay-specific wet-lab validation is not present.

## A5: evidence and literature

Evidence components remain separate. Hard constraints precede weighted ranking. Missing evidence is preserved. Weight sensitivity is available. Literature records are query/date/source/count based, with separate novelty, validation-gap and diagnostic-utility fields. PubMed and Europe PMC are supported as separate sources.

Status: implemented; manual literature review and real candidate searches are data-dependent.

## A6: baseline, ablation, stability and leakage

A conventional same-universe ranking baseline exists. Logistic and elastic-net baseline helpers are available when labelled data are supplied. Ablations, bootstrap stability, holdout guards and discovery/frozen/validation state controls are implemented.

Status: software-complete; predictive performance remains Data unavailable without labelled independent data.

## A7: final panel

A7 applies hard eligibility constraints first, ranks the eligible universe, and then optimizes patient coverage over the full eligible candidate universe when a patient-by-candidate matrix exists. Exact 0/1 optimization is used for small candidate spaces; greedy selection is used for larger spaces. The panel is capped at K <= 15 and stops when marginal gain falls below the configured threshold. Coverage-versus-K, greedy-vs-exact, bootstrap stability and optional layer-contribution diagnostics are persisted.

Artifacts include:
- final_panel.json
- final_panel_candidates.csv
- final_panel_constraints.json
- final_panel_diagnostics.json

Status: implementation complete; actual panel quality is data-dependent.

## A8: final empirical validation and reproducibility gate

A8 is an additive final gate after A7. It provides:

- sample/patient overlap auditing between discovery and independent validation;
- explicit DISCOVERY -> FROZEN -> VALIDATION state transition auditing;
- revalidation of the A7-selected candidate set;
- effect-direction concordance when effect measurements exist in both cohorts;
- bootstrap stability of validation revalidation;
- machine-readable quality-gate output;
- HTML report integration.

A8 distinguishes candidate overlap from cohort leakage. A candidate can legitimately be present in both discovery and independent validation; shared sample/patient identifiers are the leakage criterion.

The gate uses:
- PASS when independent validation inputs are present and the supplied checks pass;
- CONDITIONAL when required empirical inputs are unavailable;
- FAIL when sample/patient leakage or a reproducibility-state failure is detected.

When the CLI receives a validation-candidate file, A8 is executed automatically after A7. If that file lacks sample/patient IDs, the leakage criterion remains Data unavailable rather than assuming independence.

Artifacts include:
- a8_validation.json
- a8_leakage_audit.json
- a8_bootstrap_stability.json
- a8_generalization.json
- a8_generalization.csv
- a8_quality_gate.json

Status: implementation complete; empirical scientific conclusions remain conditional on real independent cohorts and verified metadata.

## A9: reproducibility and release gate

A9 is the final provenance layer after A8. Each completed CLI research run records the run ID, full pipeline configuration, Python/platform environment, release identity and a SHA-256 inventory of generated artifacts in `reproducibility_manifest.json`. The manifest excludes itself from its artifact inventory to avoid self-reference.

The `validate` command checks release health; the `release` command exposes the A9 readiness state. A9 does not convert software readiness into biological validation.

Status: implementation complete; reproducibility of empirical findings remains dependent on preserving the same source datasets, metadata, software environment and external resources.

## A10: real dataset intake and provenance

A10 adds a GDC/TCGA intake layer that retrieves released project metadata and
optionally inventories files through the GDC search API. It preserves source
provenance and explicit missing-data semantics and does not silently download
controlled-access data or claim that a discovered project has been biologically
analyzed.

Status: implementation complete; actual TCGA-STAD analysis remains dependent
on explicit acquisition of appropriate local files, harmonization, modality
validation and independent data.

## A11: acquisition and registration

A11 adds paginated GDC file inventory, deterministic acquisition manifests,
explicit download, checksum/size verification, controlled-access token guards,
and local dataset registration. It still does not make a file analysis-ready
without genome-build and sample-level validation.

## Explicit non-claims

The framework must not claim clinical diagnosis, clinical sensitivity/specificity/AUC, prospective utility, assay-validated LoD, independent validation results when no independent cohort is supplied, global literature novelty, or biological efficacy from synthetic software tests.

## Final acceptance rule

A passing software test suite establishes implementation behavior, not biological validity. Real datasets, verified metadata, external evidence retrieval and independent validation remain necessary before making empirical scientific claims.

Overall A0–A11 software status: GO for implementation.

Scientific-result status: conditional on real data and independent validation.
