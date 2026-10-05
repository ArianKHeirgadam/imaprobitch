"""C-12.5: formal hierarchy for external evidence sources."""
from __future__ import annotations

UNAVAILABLE = "Data unavailable"

EVIDENCE_HIERARCHY = (
    {
        "tier": 1,
        "category": "functional",
        "sources": ("VEP/Ensembl",),
        "supports": "functional consequence, transcript/protein/regulatory annotation",
        "does_not_support": "disease probability or causal clinical validity by itself",
    },
    {
        "tier": 2,
        "category": "population_identity",
        "sources": ("dbSNP",),
        "supports": "variant identity, RefSNP representation and population annotation when supplied",
        "does_not_support": "pathogenicity or cancer association by identifier presence alone",
    },
    {
        "tier": 3,
        "category": "clinical",
        "sources": ("ClinVar",),
        "supports": "reported clinical significance classifications and accessions",
        "does_not_support": "causality in the studied cohort unless independently established",
    },
    {
        "tier": 4,
        "category": "cancer_specific",
        "sources": ("cancer-specific literature",),
        "supports": "reported cancer association/evidence after explicit literature review",
        "does_not_support": "global novelty from a retrieval count alone",
    },
    {
        "tier": 5,
        "category": "cfDNA_specific",
        "sources": ("cfDNA literature / assay evidence",),
        "supports": "prior observation or assay-context evidence for liquid biopsy",
        "does_not_support": "clinical detectability without assay validation",
    },
)


def evidence_hierarchy():
    return {
        "schema_version": "c12.evidence_hierarchy.v1",
        "tiers": [dict(item) for item in EVIDENCE_HIERARCHY],
        "scientific_boundary": (
            "External databases remain typed evidence sources. Presence of a "
            "record in one source is not automatically equivalent to disease evidence."
        ),
    }


def classify_external_evidence(row):
    annotation = row.get("annotation") or {}
    functional = row.get("functional_evidence") or {}
    return {
        "functional": {
            "available": bool(functional),
            "source": "VEP/Ensembl",
            "details": functional,
        },
        "population_identity": {
            "available": bool(annotation.get("dbsnp_rsids") or annotation.get("dbsnp_ref_snp_id")),
            "source": "dbSNP",
            "details": {
                "rsids": annotation.get("dbsnp_rsids"),
                "ref_snp": annotation.get("dbsnp_ref_snp_id"),
            },
        },
        "clinical": {
            "available": bool(annotation.get("clinvar_accession") or annotation.get("clinvar_id")),
            "source": "ClinVar",
            "details": {
                "accession": annotation.get("clinvar_accession"),
                "id": annotation.get("clinvar_id"),
                "significance": annotation.get("clinical_significance"),
            },
        },
        "cancer_specific": {
            "available": bool(row.get("cancer_evidence_score") not in (None, "", UNAVAILABLE)),
            "source": "cancer-specific literature",
            "score": row.get("cancer_evidence_score", UNAVAILABLE),
        },
        "cfDNA_specific": {
            "available": bool(row.get("prior_cfdna_evidence") not in (None, "", UNAVAILABLE)),
            "source": "cfDNA literature / assay evidence",
            "score": row.get("prior_cfdna_evidence", UNAVAILABLE),
        },
    }
