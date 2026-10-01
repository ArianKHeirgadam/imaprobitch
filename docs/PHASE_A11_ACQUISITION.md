# Phase A11 — GDC Acquisition, Verification & Dataset Registration

A11 turns the A10 GDC project/file discovery layer into a controlled, reproducible acquisition workflow.

## What A11 does

1. Paginated GDC file inventory for a project.
2. Modality classification: SNV/INDEL, CNV, METHYLATION, SV, CLINICAL, BIOSPECIMEN, OTHER.
3. Deterministic acquisition manifest.
4. JSON and TSV manifest outputs.
5. Explicit download command; discovery never downloads biological files.
6. Open-access downloads through the GDC data/{file_uuid} endpoint.
7. Controlled-access downloads require GDC_TOKEN or an explicit token.
8. MD5 and file-size verification after download.
9. Failed checksum verification does not register the file as analysis-ready.
10. Dataset registration records verified local files while leaving genome-build and sample-manifest validation unavailable until those properties are actually inspected.

The GDC API documentation specifies UUID-based downloads through the data endpoint and states that controlled-access downloads require an authentication token.

## Step 1 — Inventory

PowerShell:

    $env:PYTHONPATH="."
    python -m wgr_cdp.cli inventory --project TCGA-STAD --output results/tcga_stad_inventory

For open-access SNV/INDEL candidates:

    python -m wgr_cdp.cli inventory --project TCGA-STAD --access open --modality SNV_INDEL --output results/tcga_stad_snv_indel

Optional filters: --category, --strategy, --format, --max-files, --modality.

## Step 2 — Acquisition

Acquisition is an explicit second command:

    python -m wgr_cdp.cli acquire --manifest results/tcga_stad_snv_indel.json --output data/raw/tcga_stad

For controlled-access files, use an environment variable rather than committing the token:

    $env:GDC_TOKEN="YOUR_TOKEN"
    python -m wgr_cdp.cli acquire --manifest results/tcga_stad_inventory.json --output data/raw/tcga_stad

Never commit the token or place it in a manifest.

## Step 3 — Registration

    python -m wgr_cdp.cli register --manifest results/tcga_stad_snv_indel.json --root data/raw/tcga_stad --output results/tcga_stad_registration.json

Registration only accepts files whose local download was verified. It does not declare them scientifically analysis-ready until genome-build and sample-manifest validation are performed.

## Scientific guardrails

A11 does not treat project-level case counts as usable SNV/INDEL sample counts, infer a matched tumor/normal cohort from file counts, infer genome build from filename alone, turn unavailable metadata into negative evidence, claim clinical validity, claim cfDNA detectability from tissue-only files, or download all project files automatically.

## Acceptance status

- [x] Paginated GDC inventory.
- [x] Modality classification.
- [x] Acquisition manifest.
- [x] Explicit download step.
- [x] Controlled-access token guard.
- [x] MD5 and size verification.
- [x] Dataset registration.
- [x] Unit tests.
- [ ] Genome-build/sample-level validation on acquired real files.
- [ ] Real TCGA-STAD SNV/INDEL cohort construction.
- [ ] Real CNV cohort construction.
- [ ] Independent validation cohort.
- [ ] Empirical cfDNA/plasma validation.

The unchecked items are deliberately data-dependent.
