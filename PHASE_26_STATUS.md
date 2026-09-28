# Phase 26 — Real End-to-End VCF Analysis

Phase 26 connects real VCF input to the existing WGR-CDP analysis components.

## Real workflow

1. Read one-sample VCF files from healthy/control and cancer/case directories.
2. Normalize and deduplicate variants per sample.
3. Compare carrier frequencies between cohorts.
4. Compute Fisher exact p-values.
5. Apply Benjamini-Hochberg FDR correction.
6. Build candidate profiles and evidence scores.
7. Optionally query ClinVar, dbSNP, and Ensembl VEP with `--annotate`.
8. Write CSV, JSON, and HTML results.

## Run

    python -m wgr_cdp.cli run --healthy data/healthy --cancer data/cancer --output results/run_001

Optional external annotation:

    python -m wgr_cdp.cli run --healthy data/healthy --cancer data/cancer --output results/run_001 --annotate

## Output

- `variants.csv`
- `significant_variants.csv`
- `genes.csv`
- `significant_genes.csv`
- `candidates.csv`
- `annotations.json`
- `summary.json`
- `run.json`
- `report.html`

The built-in VCF reader currently expects uncompressed `.vcf` files with at least the eight mandatory VCF columns. The analysis treats each VCF file as one sample.

This is a research analysis workflow, not a clinical diagnostic system.
