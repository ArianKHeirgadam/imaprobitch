# Release 1.3.0

This release marks the current WGR-CDP implementation as a **research
bioinformatics framework**.

## Included layers

- VCF ingestion and normalization
- Quality control and reference validation
- Annotation and feature fusion
- ClinVar, dbSNP, and Ensembl VEP evidence integration
- Case/control cohort comparison
- Fisher exact testing
- Benjamini-Hochberg FDR correction
- Candidate evidence aggregation and prioritization
- Pipeline execution hardening
- Run tracking and validation
- A8 independent-validation and leakage gate
- A9 reproducibility manifest and release-readiness gate
- A10 GDC/TCGA dataset intake and provenance
- A11 GDC acquisition, checksum verification and dataset registration

## Validation

Run the complete test suite from the repository root:

```powershell
$env:PYTHONPATH="."
pytest tests -v
```

The release health check can be executed with:

```python
from wgr_cdp.release import run_health_check
print(run_health_check())
```

A completed research run writes `reproducibility_manifest.json` containing the run ID, configuration, software environment, and SHA-256 hashes of generated artifacts.

The A9 release-readiness check is:

```powershell
python -m wgr_cdp.cli release
```

## Scientific scope

The framework supports genomic research, cfDNA-aware candidate discovery and panel design. It does
not establish clinical diagnosis, clinical validity, causal relationships, or
clinical utility.

A candidate score is a transparent research prioritization score and must not
be interpreted as a disease probability.
