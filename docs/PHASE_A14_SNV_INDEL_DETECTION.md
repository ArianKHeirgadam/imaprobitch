# Phase A14 — SNV/INDEL Detection Engine

## Scope
A14 implements the PDF-defined SNV/INDEL feature-extraction and cohort-detection
layer on called VCF/VCF.GZ inputs. It is not a raw FASTQ/BAM variant caller.

## Pipeline
VCF/VCF.GZ -> PASS/QC -> SNV/INDEL extraction -> patient observations ->
case/control comparison -> Fisher exact -> BH-FDR -> detection artifacts.

## Scientific rules
- Only explicit PASS or "." records are admitted.
- Multi-allelic SNV/INDEL alleles are separated.
- Depth/VAF filters are optional and never convert missing values to negatives.
- Missing/unknown observations remain unavailable.
- Cancer and healthy/control groups are explicit inputs.
- Statistics are patient-level through the existing scanner.
- Multiple testing uses Benjamini-Hochberg.
- No clinical sensitivity/specificity claim is produced.
- This engine consumes called variants; it does not invent variant calls.

## Outputs
- snv_indel_observations.csv: auditable observation layer.
- snv_indel_detection.csv: case/control statistics and FDR.


## Real-data validation

The real-data validation command is intentionally cancer-side only when an
independent healthy/control VCF is unavailable:

```powershell
.\venv\Scripts\python.exe -m wgr_cdp.cli snv-indel-validate `
  --cancer data/real/tcga_stad_subset_20_normalized `
  --output results/a14_tcga_stad_real_validation
```

It writes `snv_indel_real_validation.json` and reports sample/observation,
SNV/INDEL, status, and chromosome counts. It explicitly records the control
status as `Data unavailable` rather than treating TCGA matched normals or
1000 Genomes as an independent gastric healthy cohort.

Cancer-vs-control detection remains available through
`snv-indel-detect` when an explicit independent control VCF cohort is
provided.
