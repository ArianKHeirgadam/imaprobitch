# Phase A13 — Reference-Aware Variant Normalization

## Scope

This phase upgrades the GDC masked somatic MAF -> adapter-VCF path with a deterministic,
reference-aware normalization layer.

The normalizer is deliberately conservative. A VCF is not considered biologically
normalized merely because it passed structural QC.

## Implemented

- GRCh38 FASTA is supplied explicitly at runtime.
- REF is checked against the supplied reference sequence.
- Chromosome aliases `1` / `chr1` are resolved.
- Common-prefix and common-suffix bases are minimally trimmed.
- Simple insertions/deletions are left-aligned through repeat contexts.
- Multiallelic VCF records are expanded one ALT at a time.
- Equivalent records are deduplicated after normalization.
- Output contains normalization/reference-check/original-variant provenance in INFO.
- A SHA-256 digest of the reference FASTA is written to the normalization manifest.
- Per-file and batch normalization manifests are emitted.
- Reference mismatch is a hard scientific failure; the record is never silently relabelled as normalized.

## CLI

Single VCF:

```powershell
.\venv\Scripts\python.exe -m wgr_cdp.cli normalize-vcf \
  --input data/real/tcga_stad_wxs_vcf/sample.vcf \
  --output data/real/tcga_stad_wxs_normalized/sample.vcf \
  --reference data/reference/GRCh38.fa \
  --reference-build GRCh38
```

Batch:

```powershell
.\venv\Scripts\python.exe -m wgr_cdp.cli normalize-vcf-batch \
  --input data/real/tcga_stad_wxs_vcf \
  --output data/real/tcga_stad_wxs_normalized \
  --reference data/reference/GRCh38.fa \
  --reference-build GRCh38
```

Use an analysis-compatible GRCh38/hg38 reference. UCSC identifies hg38 as
GRCh38 and publishes reference FASTA resources; GATK likewise supports GRCh38/hg38
and emphasizes reference compatibility for downstream analysis.

## Scientific gate

Until a real GRCh38 FASTA has been supplied and all variants pass REF validation,
the pipeline must retain the state `normalization_required` or `CONDITIONAL`.
No candidate discovery or biological interpretation should treat adapter VCFs as
fully normalized before this gate passes.

The current open-access MAF acquisition is a somatic-MAF fallback. It is not raw WGS
VCF data, and paired TCGA normals are not an independent healthy population.
