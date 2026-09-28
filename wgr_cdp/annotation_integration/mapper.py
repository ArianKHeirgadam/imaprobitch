"""Normalize annotation records into a stable internal representation."""


def map_annotation(annotation):
    """Map an annotation record to the stable WGR-CDP annotation schema."""
    annotation = annotation or {}
    mapped = {
        "gene": annotation.get("gene"),
        "consequence": annotation.get("consequence"),
        "impact": annotation.get("impact"),
        "source": annotation.get("source"),
    }

    # Preserve provider-specific identifiers when available.
    for key in (
        "clinvar_id",
        "clinvar_accession",
        "dbsnp_rsids",
        "dbsnp_ref_snp_id",
        "dbsnp_variant_type",
    ):
        if key in annotation:
            mapped[key] = annotation[key]

    return mapped
