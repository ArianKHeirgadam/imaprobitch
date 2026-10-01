# Phase A12 — Real GDC Case/Sample/File Cohort Construction

A12 converts GDC project metadata into a real case/sample/file analysis manifest.

## Design

The project-level GDC case count is never used as the number of analyzable tumor or normal samples. A12 queries the GDC cases endpoint for explicit case/sample metadata and the files endpoint for variant-file provenance.

Each sample retains case UUID, case submitter ID, sample UUID, sample submitter ID, sample type, tissue type, tumor descriptor, preservation method, FFPE metadata when available, explicit sample classification and exclusion reasons.

Sample classification is metadata-driven:

- Primary Tumor / recurrent tumor -> TUMOR
- Solid Tissue Normal / normal tissue -> NORMAL
- metastatic -> TUMOR_METASTATIC
- explicit tumor descriptor -> TUMOR
- otherwise -> UNCLASSIFIED

Unclassified samples are retained with an exclusion reason; they are not silently converted into normal or tumor samples.

Variant files retain GDC file UUID, filename, size, checksum, access, data category/type/format, experimental strategy, workflow provenance and case/sample associations when supplied by GDC.

## Run

From the project root:

    $env:PYTHONPATH="."
    python -m wgr_cdp.cli cohort --project TCGA-STAD --output results/tcga_stad_cohort.json

For open-access files only:

    python -m wgr_cdp.cli cohort --project TCGA-STAD --access open --output results/tcga_stad_open_cohort.json

## What the output means

The output is a cohort manifest, not a biological result.

Important fields:

- case_count_observed: unique cases represented by returned sample metadata
- sample_count: unique case/sample pairs
- tumor_sample_count
- normal_sample_count
- excluded_sample_count
- variant_files
- analysis_ready: false

A12 deliberately keeps analysis_ready=false until local acquisition, genome-build validation, sample-level QC and file-to-sample verification are completed.

## Next transition

The next real-data layer must:

1. acquire a scientifically defined set of variant files;
2. inspect actual VCF/MAF headers and genome build;
3. validate tumor/normal pairing where available;
4. reject duplicates and invalid files with explicit reasons;
5. construct the usable SNV/INDEL cohort;
6. feed only validated local data into the existing discovery/statistics stack.

No A12 count should be interpreted as a clinical performance result or as evidence that the final candidate panel works on patients.
