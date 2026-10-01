# Phase A10 — Real Dataset Intake and Provenance

A10 begins the real-data execution track after A0–A9 software completion.

## Scope

A10 adds a reproducible GDC/TCGA intake layer for released project metadata and
file inventory discovery. It does **not** silently download controlled-access
biological data and does not manufacture cohort counts.

The GDC API exposes project, case, and file search/retrieval endpoints and
supports project metadata retrieval by `project_id`. File manifests can be
generated for downstream acquisition; controlled-access downloads require
authentication.

## Implemented

- GDC project metadata retrieval.
- GDC file inventory query filtered by project.
- Optional `open` / `controlled` file-access filter.
- Machine-readable A10 intake record.
- Explicit `downloaded_locally: false` provenance state.
- Missing biological/clinical results remain `Data unavailable`.
- No biological analysis is performed by the intake layer.
- CLI integration.

## CLI

```powershell
$env:PYTHONPATH="."
python -m wgr_cdp.cli intake --project TCGA-STAD --output results/tcga_stad_intake.json
```

To inventory only open-access files:

```powershell
python -m wgr_cdp.cli intake --project TCGA-STAD --file-access open --output results/tcga_stad_open_files.json
```

The command writes an intake JSON record containing the project identity,
release state, source metadata, summary counts supplied by GDC, and optional
file inventory metadata.

## Scientific boundary

A10 is dataset acquisition/provenance infrastructure. A successful GDC query
does not mean that a usable SNV, INDEL, CNV, methylation, plasma, or matched
normal cohort has been downloaded or analyzed.

Actual scientific analysis begins only after local files are explicitly
acquired, validated, harmonized and passed through the appropriate modality
pipeline.

## Acceptance criteria

- [x] GDC project endpoint integration.
- [x] GDC file endpoint integration.
- [x] Provenance-preserving intake schema.
- [x] Explicit missing-data semantics.
- [x] CLI integration.
- [x] Unit tests without network dependence.
- [ ] Actual local TCGA-STAD biological analysis.
- [ ] Independent validation cohort.
- [ ] Assay-specific empirical cfDNA validation.

The remaining unchecked items require actual datasets and are not replaced by
synthetic fixtures.
