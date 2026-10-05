# A12 Status — Real Data Acquisition

## Phase status
Implementation: COMPLETE
Local regression: PASS — 387 passed in 2.44s
Phase status: CLOSED

## Implementation

The project now contains a reproducible multi-source real-data acquisition layer.

| Component | Status |
|---|---|
| TCGA-STAD source profile | COMPLETE |
| GDC inventory / acquisition reuse | COMPLETE |
| 1000 Genomes 30x GRCh38 source profile | COMPLETE |
| Deterministic 1000G sample selection | COMPLETE |
| 1000G VCF subsetting | COMPLETE |
| GTEx Stomach reference profile | COMPLETE |
| GDC masked MAF to per-sample VCF adapter | COMPLETE |
| CLI integration | COMPLETE |
| Network-independent tests | COMPLETE |

## Data-dependent work

- Actual TCGA-STAD file acquisition.
- Actual 1000G download.
- Actual genome-build/reference validation.
- Population matching and confounder review.
- Real Cancer-vs-reference analysis.
- Independent validation cohort.
- Empirical cfDNA/plasma evidence.

## Scientific boundary

This phase provides acquisition and harmonization infrastructure. It does not claim that any downloaded population reference is automatically an appropriate healthy control, and it does not claim empirical cfDNA detectability.