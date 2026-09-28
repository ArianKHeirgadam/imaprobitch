# Phase 28 — Real SNV + INDEL Cohort Analysis

Phase 28 upgrades the real analysis path from presence-only VCF parsing to explicit biallelic variant representation and genotype-aware cohort ingestion.

## Added

- multi-allelic ALT decomposition into independent variants
- SNV vs INDEL classification
- `.vcf` and `.vcf.gz` input
- multi-sample VCF support using GT when FORMAT/sample columns are present
- carrier assignment per sample from genotype
- backward-compatible single-sample 8-column VCF handling
- variant type in analysis output

## Real consequence

A multi-sample VCF is no longer treated as one patient. For example, `C1=1/1` and `C2=0/0` produce one cancer carrier and one non-carrier.

The main CLI continues to be:

    python -m wgr_cdp.cli run --healthy data/healthy --cancer data/cancer --output results/run_001

This phase still treats SNV/INDEL observations as cohort carrier features. CNV, SV, methylation, mitochondrial and fragmentomic modalities remain handled by the multimodal feature-table path and are separate from VCF genotype parsing.
