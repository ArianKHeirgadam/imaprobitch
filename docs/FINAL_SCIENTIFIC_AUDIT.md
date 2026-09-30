# WGR-CDP Final Scientific Audit — A0 to A7

## Scope

This audit compares the implemented research framework against the supplied WGR-CDP specification and its stated scientific boundary. The project remains a computational candidate-discovery and panel-design framework, not a clinical diagnostic system.

## A0–A2: discovery and benchmark

- Repository/data-governance infrastructure exists.
- Exact discovery and multi-resolution discovery are implemented.
- Resolutions are 5 Mb, 1 Mb, 100 kb, 10 kb, 1 kb, and base/breakpoint.
- Final coarse-to-fine hits are exact-checked.
- Benchmarking reports recall/precision, runtime, peak memory, evaluated regions, feature-type breakdown and parameter sweeps.
- Measured poor recall is not silently converted into success.

**Status: implemented; biological performance remains data-dependent.**

## A3: blood background

WBC, healthy-plasma, PoN, gnomAD and CHIP/background fields are represented independently. Missing sources remain Data unavailable and are not treated as negative evidence.

**Status: implemented; real background data are required for biological conclusions.**

## A4: cfDNA detectability

The required tumor-fraction grid (0.5 through 0.005), sequencing depth, region size, informative sites, copy number, assay error and blood-background penalty are represented. Analytical detectability is compared with Monte-Carlo simulation. Low-pass SNV/INDEL limitations are explicitly marked.

**Status: implemented as a computational research model; assay-specific wet-lab validation is not present.**

## A5: evidence and literature

Evidence components remain separate. Hard constraints precede weighted ranking. Missing evidence is preserved. Weight sensitivity is available. Literature records are query/date/source/count based, with separate novelty, validation-gap and diagnostic-utility fields. PubMed and Europe PMC are supported as separate sources.

**Status: implemented; manual literature review and real candidate searches are data-dependent.**

## A6: baseline, ablation, stability and leakage

A conventional same-universe ranking baseline exists. Logistic and elastic-net baseline helpers are available when labelled data are supplied. Ablations, bootstrap stability, holdout guards and discovery/frozen/validation state controls are implemented.

**Status: software-complete; predictive performance remains Data unavailable without labelled independent data.**

## A7: final panel

A7 applies hard eligibility constraints first, ranks the eligible universe, and then optimizes patient coverage over the full eligible candidate universe when a patient-by-candidate matrix exists. Exact 0/1 optimization is used for small candidate spaces; greedy selection is used for larger spaces. The panel is capped at K <= 15 and stops when marginal gain falls below the configured threshold. Coverage-versus-K, greedy-vs-exact, bootstrap stability and optional layer-contribution diagnostics are persisted.

Artifacts include:
- final_panel.json
- final_panel_candidates.csv
- final_panel_constraints.json
- final_panel_diagnostics.json

**Status: implementation complete; actual panel quality is data-dependent.**

## Explicit non-claims

The framework must not claim clinical diagnosis, clinical sensitivity/specificity/AUC, prospective utility, assay-validated LoD, independent validation results when no independent cohort is supplied, global literature novelty, or biological efficacy from synthetic software tests.

## Final acceptance rule

A passing software test suite establishes implementation behavior, not biological validity. Real datasets, verified metadata, external evidence retrieval and independent validation remain necessary before making empirical scientific claims.

**Overall A0–A7 software status: GO for implementation. Scientific-result status: conditional on real data and external validation.**