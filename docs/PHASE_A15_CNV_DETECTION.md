# A15 — CNV Detection / Validation

## Scope

A15 adds a research-grade CNV segment validation layer using real CNV data. Event-level carrier analysis and continuous dosage analysis are separate contracts.

### Event-level
- GAIN/LOSS carriers
- explicit region denominators
- Fisher exact test
- carrier-frequency effect size
- Benjamini-Hochberg q-values

### Dosage-level
- numeric log2_ratio / Segment_Mean
- mean difference
- standardized mean difference
- reproducible permutation test
- Benjamini-Hochberg q-values

These signals are never collapsed into one statistic.

## TCGA/GDC compatibility

GDC documents CNV segment files with chromosome/start/end and Segment_Mean; Segment_Mean represents log2(copy-number / 2). The parser also accepts explicit copy number. Supported aliases include GDC_Aliquot_ID, Chromosome, Start, End, Segment_Mean, Copy Number, Gene Name, sample_id and group.

## Missingness

Missing segments are Data unavailable, never neutral or zero. Event denominators require an explicit regional state. Dosage denominators require an explicit numeric dosage.

## Comparator semantics

Tumor/case is compared with an explicitly supplied comparator. A matched normal is not relabelled as an independent healthy population. Independent healthy CNV data remain Data unavailable unless supplied.

## Provenance

Validation artifacts record source paths, SHA-256 hashes, row counts, permutation count, seed and schema version.

## CLI

PowerShell example:

`.\venv\Scripts\python.exe -m wgr_cdp.cli cnv-validate --input <TCGA-CNV.tsv> --output results/a15_cnv_validation --metadata <sample_groups.csv> --alpha 0.05 --permutations 999 --seed 42`

sample_groups.csv must provide sample_id and group (tumor/case or comparator/normal).

## Scientific boundary

A15 does not establish biomarker status, clinical validity, clinical sensitivity/specificity, or independent healthy-population inference.