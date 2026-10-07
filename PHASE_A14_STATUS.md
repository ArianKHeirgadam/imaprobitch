# Phase A14 — SNV/INDEL Detection Engine

Status: **PASS / CONDITIONAL**

## Completed

- VCF/VCF.GZ SNV/INDEL extraction
- PASS/`. ` filter semantics
- multi-allelic decomposition
- GT/DP/AD/AF parsing
- optional depth/VAF thresholds
- explicit missing/unavailable semantics
- patient-level case/control statistics through the existing exact scanner
- BH-FDR
- auditable CSV artifacts
- CLI routing and regression coverage
- real cancer-side validation of normalized TCGA-STAD open-access subset
- scientific audit of the real validation boundary
- explicit refusal to invent an independent healthy/control cohort

## Verified local state

- Full test suite: **421 passed**
- Real normalized inputs: **19 VCF files**
- Variant observations: **8,687**
- SNV observations: **7,132**
- INDEL observations: **1,555**
- Detected observations: **8,687**
- Unavailable observations: **0**
- Chromosomes represented: **24**
- GRCh38 reference-aware normalization upstream: **PASS**
- Reference mismatch upstream: **0**

## Scientific interpretation

The real validation is a **cancer-side technical/feature-extraction validation** of the deterministic 20-case open-access TCGA-STAD subset.

The 20-case subset contained one valid empty MAF source, so 19 variant-bearing normalized VCFs were produced. The empty source is treated as **empty/unavailable input**, not as a negative cancer sample.

The 8,687 records are somatic variant observations carried forward from the GDC masked somatic MAF fallback. Therefore:

- `detected_count=8687` means the supplied somatic records were successfully represented as detected variant observations.
- It is **not** a raw-read sensitivity estimate.
- It is **not** a clinical detection rate.
- It is **not** evidence that every TCGA case carries every reported variant.
- `sample_count=19` means 19 non-empty validation inputs contributed variant observations; it is not the size of an independent healthy cohort.

## Cancer-vs-healthy boundary

`control_status = Data unavailable` is intentional.

The available TCGA matched normals are paired non-tumor comparators, not an independent healthy population. The open somatic MAF fallback does not provide an independent healthy VCF cohort.

Therefore A14 does **not** report cancer-vs-healthy inference on the real subset.

1000 Genomes may be used as a population/germline reference, but must not be relabeled as a gastric healthy cohort.

## Closure criterion

A14 is considered **PASS / CONDITIONAL**:

- software implementation: PASS
- regression suite: PASS
- real cancer-side validation: PASS
- scientific integrity boundary: PASS
- independent healthy/control validation: **CONDITIONAL on future data availability**

A future independent healthy/control VCF cohort can activate the existing `snv-indel-detect` cancer-vs-control path without changing the scientific interpretation of this A14 validation.
