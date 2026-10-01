"""Final release health checks."""

from .metadata import RELEASE_METADATA


REQUIRED_COMPONENTS = {
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
}


def run_health_check():
    """Return deterministic release readiness checks."""
    components = set(RELEASE_METADATA.get("components", []))
    checks = {
        "metadata_complete": bool(
            RELEASE_METADATA.get("name")
            and RELEASE_METADATA.get("release")
            and RELEASE_METADATA.get("status")
        ),
        "required_components_declared": REQUIRED_COMPONENTS <= components,
        "research_scope_declared": (
            RELEASE_METADATA.get("status") == "research"
            and RELEASE_METADATA.get("clinical_diagnostic") is False
        ),
    }
    return {
        "release": RELEASE_METADATA["release"],
        "passed": all(checks.values()),
        "checks": checks,
    }
