# A12 — Real Data Acquisition: TCGA-STAD + 1000 Genomes + GTEx

A12 is the real-data execution layer after the software hardening phases.

## Recommended source roles

### 1. Cancer discovery — TCGA-STAD

Primary source: GDC project TCGA-STAD.

The GDC project exposes Stomach Adenocarcinoma data, including copy-number and simple-nucleotide-variation categories. Public masked somatic MAF files are available; controlled-access data require authorization.

Preferred order:

1. File-level WGS somatic VCF when the selected files are actually WGS and access is authorized.
2. Public GDC Masked Somatic Mutation MAF as a reproducible open-access fallback.

The MAF fallback is not labelled as raw WGS. It is converted only to an adapter VCF and remains marked as requiring reference-aware normalization.

## 2. Population / germline reference — 1000 Genomes 30x

Source: IGSR / 1000 Genomes 30x on GRCh38.

A12 uses the 2504 unrelated phase-3 panel as the default public high-coverage reference population and can deterministically select a smaller subset, for example 250 samples, balanced across AFR, AMR, EAS, EUR and SAS.

This cohort is labelled Population/germline reference cohort, not automatically disease-matched healthy control.

A formal Cancer-vs-Healthy interpretation still requires review of population background, sample type, pipeline, coverage and other technical factors.

## 3. Tissue reference — GTEx Stomach

GTEx provides non-diseased tissue references including stomach.

A12 records GTEx as a Non-diseased tissue reference. Raw DNA/RNA sequence data and full donor metadata are protected-access, so A12 never silently treats an open GTEx download as a public healthy-WGS VCF cohort.

## Step 1 — Write the study data plan

~~~powershell
$env:PYTHONPATH="."
python -m wgr_cdp.cli data-plan --output results/data_plan.json --healthy-samples 250
~~~

## Step 2 — Discover TCGA-STAD files

~~~powershell
python -m wgr_cdp.cli inventory --project TCGA-STAD --access open --modality SNV_INDEL --output results/tcga_stad_snv_indel
python -m wgr_cdp.cli inventory --project TCGA-STAD --access open --modality CNV --output results/tcga_stad_cnv
~~~

## Step 3 — Acquire verified GDC files

~~~powershell
python -m wgr_cdp.cli acquire --manifest results/tcga_stad_snv_indel.json --output data/raw/tcga_stad
~~~

Controlled-access:

~~~powershell
$env:GDC_TOKEN="YOUR_GDC_TOKEN"
python -m wgr_cdp.cli acquire --manifest results/tcga_stad_inventory.json --output data/raw/tcga_stad
~~~

## Step 4 — Build the GDC cohort manifest

~~~powershell
python -m wgr_cdp.cli cohort --project TCGA-STAD --output results/tcga_stad_cohort.json
~~~

## Step 5 — Download public 1000G GRCh38 reference

For an integration smoke test, start with three chromosomes:

~~~powershell
python -m wgr_cdp.cli 1000g-manifest --output results/1000g_30x_manifest.json --samples 250 --chromosomes 1,2,3
python -m wgr_cdp.cli reference-acquire --manifest results/1000g_30x_manifest.json --output data/raw/1000g_30x
~~~

For the whole autosomal + X reference, omit --chromosomes. Whole-genome files are large and acquisition is deliberately explicit.

## Step 6 — Select the 250 1000G samples

Save the public sample panel URL recorded in the manifest as data/raw/1000g_30x/integrated_call_samples_v3.20130502.ALL.panel, then run:

~~~powershell
python -m wgr_cdp.cli 1000g-select --panel data/raw/1000g_30x/integrated_call_samples_v3.20130502.ALL.panel --output results/1000g_250_samples.txt --samples 250
~~~

## Step 7 — Subset each downloaded multi-sample VCF

The library function subset_vcf_samples can create a 250-sample VCF from each downloaded chromosome file while preserving all VCF headers and genotype columns.

## Step 8 — Convert an open TCGA masked MAF when WGS VCF is unavailable

~~~powershell
python -m wgr_cdp.cli maf-to-vcf --input data/raw/tcga_stad/YOUR_MASKED_SOMATIC.maf.gz --output data/cancer/tcga_stad_vcf
~~~

The adapter preserves source provenance and explicitly marks reference-aware normalization as required.

## Target local layout

~~~text
data/
├── cancer/
│   └── tcga_stad_vcf/
├── healthy/
│   └── 1000g_250/
├── cnv/
├── reference/
└── validation/

results/
├── data_plan.json
├── tcga_stad_cohort.json
├── tcga_stad_snv_indel.json
├── tcga_stad_cnv.json
└── 1000g_250_samples.txt
~~~

## Scientific guardrails

- 1000 Genomes is a population/germline reference unless the study explicitly justifies it as a comparator.
- GTEx is a non-diseased tissue reference; raw WGS is protected access.
- Open TCGA masked MAF is public somatic data, not raw WGS VCF.
- Missing metadata remains Data unavailable.
- Genome build is never inferred from a filename.
- No cfDNA detectability claim is derived merely from tissue WGS.
- A final Cancer-vs-reference statistical claim requires cohort harmonization and confounding review.
- Independent validation remains a separate frozen-panel step.