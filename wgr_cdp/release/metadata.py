"""Release metadata for the WGR-CDP research framework."""

RELEASE_METADATA = {
    "name": "WGR-CDP",
    "release": "1.1.0",
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
    ],
}
