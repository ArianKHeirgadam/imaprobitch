"""Normalize annotation records into a stable internal representation."""


def map_annotation(annotation):
    """Map an annotation record to the WGR-CDP annotation schema."""
    annotation = annotation or {}
    return {
        "gene": annotation.get("gene"),
        "consequence": annotation.get("consequence"),
        "impact": annotation.get("impact"),
        "source": annotation.get("source"),
    }
