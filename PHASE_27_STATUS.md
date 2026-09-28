# Phase 27 — WGR-CDP multimodal real analysis

This phase implements the missing real-analysis layers identified in the repository audit: multimodal feature ingestion, genome-wide multi-resolution scanning, patient × candidate matrix construction, complementary panel optimization, and cfDNA detectability/LoD research modelling.

## Supported normalized feature types

- SNV
- INDEL
- CNV
- SV
- METHYLATION
- MITOCHONDRIAL
- FRAGMENTOMICS (when source data are available)

The normalized feature CSV requires:

`patient,group,stage,region,feature_type,value,status`

Optional columns include `tumor_fraction,depth,error_rate,blood_background,validation_status,assay,chrom,start,end`.

`status` must be `Detected`, `Not detected`, or `Data unavailable`.

## Multi-resolution scan

Regions are evaluated at 5Mb, 1Mb, 100kb, 10kb, and 1kb resolutions, with base/breakpoint resolution retained in the input feature itself.

## Detectability

The research model evaluates tumor fractions including 0.5, 0.25, 0.1, 0.05, 0.02, 0.01 and 0.005, using depth, error rate and minimum alternate-read assumptions. It also estimates a computational LoD at a target power of 0.95.

## Panel

A patient × candidate matrix is generated and a deterministic greedy complementary panel is selected with `K <= 15` by default.

## Run

    python -m wgr_cdp.cli run --healthy data/healthy --cancer data/cancer --features data/features.csv --metadata data/metadata.csv --output results/full_run --max-panel-size 15 --depth 300

The multimodal outputs are written under `results/full_run/multimodal/`.

These outputs are research computational results and are not clinical diagnostic claims. Assay-specific validation is required for LoD/power interpretation.
