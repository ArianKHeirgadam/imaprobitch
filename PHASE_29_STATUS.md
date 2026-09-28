# Phase 29 — Real CNV Analysis

## Goal
Add real CNV segment ingestion and Cancer-vs-Healthy CNV comparison without inventing biological results.

## Implemented
- CSV/TSV CNV ingestion.
- Chromosome normalization and segment validation.
- Explicit GAIN/LOSS/NEUTRAL classification from copy number or log2 ratio.
- Real cohort-level CNV carrier frequencies.
- Fisher exact testing and Benjamini-Hochberg FDR.
- Optional gene-level events when genes are supplied in the CNV input.
- Significant CNV table and deterministic research candidate ranking.

## Outputs
- cnv_segments.csv
- cnv_gene_events.csv
- cnv_region_comparison.csv
- significant_cnvs.csv
- cnv_candidates.csv

## Scientific limitations
- Exact segment coordinates are compared as supplied.
- Gene-level results require gene information in the input.
- No synthetic gene annotation is created.
- CNV normalization is not a substitute for assay-specific segmentation/purity/ploidy modeling.
- Candidate scores are research prioritization signals, not clinical probabilities.

## Acceptance
- [x] Real CNV parser
- [x] Cancer/Healthy comparison
- [x] Fisher exact testing
- [x] FDR correction
- [x] Real output artifacts
- [x] Tests
- [ ] CLI integration remains to be completed in this phase
