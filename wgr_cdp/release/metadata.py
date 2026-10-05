"""Release metadata for the WGR-CDP research framework."""

RELEASE_METADATA = {
    "name": "WGR-CDP",
    "release": "1.4.0",
    "status": "research",
    "scope": "genomic cohort analysis, cfDNA-aware candidate discovery and panel design",
    "clinical_diagnostic": False,
    "components": [
        "VCF ingestion",
        "ClinVar integration",
        "dbSNP integration",
        "Ensembl VEP functional evidence",
        "case/control cohort comparison",
        "Fisher exact testing",
        "Benjamini-Hochberg FDR correction",
        "candidate evidence prioritization",
        "pipeline validation and run tracking",
        "A8 empirical validation and leakage gate",
        "A9 reproducibility manifest and release gate",
        "A10 GDC/TCGA dataset intake and provenance",
        "A11 GDC acquisition, checksum verification and dataset registration",
        "A12 real GDC case-sample-file cohort construction",
        "C-11 end-to-end integration and artifact contract",
    ],
}
