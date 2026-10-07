# A14 Scientific Audit — SNV/INDEL Detection

## Audit result

**PASS / CONDITIONAL**

The A14 implementation and real cancer-side validation satisfy the current data boundary without fabricating a healthy cohort.

## Evidence reviewed

- Full local test suite: **421 passed**
- Real validation command: `snv-indel-validate`
- Normalized TCGA-STAD open-access subset
- Upstream A13 GRCh38 reference-aware normalization result

## Real validation

| Metric | Result |
|---|---:|
| Input files | 19 |
| Samples represented | 19 |
| Variant observations | 8,687 |
| SNVs | 7,132 |
| INDELs | 1,555 |
| Detected | 8,687 |
| Data unavailable | 0 |
| Chromosomes | 24 |
| Independent healthy control | Data unavailable |

The SNV + INDEL totals reconcile exactly:

`7,132 + 1,555 = 8,687`

The status counts also reconcile with the observation count:

`8,687 detected + 0 unavailable = 8,687`

## Double-counting boundary

The selected real subset was constructed deterministically by biological case and one open WXS representation per eligible case. A13 reference-aware conversion and normalization preserved the 8,687 records with zero reference mismatches and no reported normalization deduplication loss.

The A14 validation therefore verifies that the normalized records can be parsed and classified without silently dropping them.

This does not establish that the underlying biological cohort has no duplicate biological calls across independent upstream callers, because the validation input is the selected single representation per case.

## Detection semantics

The validation consumes **called somatic variants**, not FASTQ/BAM read evidence.

Consequently, every accepted MAF-derived record being classified as `Detected` is an observation of an upstream somatic call. It must not be interpreted as:

- variant-calling sensitivity;
- sequencing sensitivity;
- clinical diagnostic sensitivity;
- prevalence in the entire TCGA-STAD population.

## Missingness semantics

An empty source is not converted to a negative observation. Missing or unavailable information is not treated as absence.

This preserves the project rule:

**missing ≠ negative**

## Healthy-control integrity

No independent healthy VCF was available for this real validation.

Matched TCGA normal material remains a paired comparator and is not relabeled as an independent healthy population. Population resources such as 1000 Genomes likewise remain population/germline references rather than gastric healthy controls.

## Final decision

**A14 = PASS / CONDITIONAL**

The implementation is ready for downstream work on the cancer-side discovery representation.

Cancer-vs-independent-healthy statistical inference remains gated on acquisition of an appropriate independent control cohort.
