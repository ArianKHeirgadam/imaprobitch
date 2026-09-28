"""Connect normalized variants to annotation adapters."""

from .mapper import map_annotation


def annotate_variants(variants, adapter):
    """Annotate variants using an adapter callable.

    The adapter receives one normalized variant and may return a mapping or None.
    Missing annotations are represented by the stable empty schema.
    """
    results = []
    for variant in variants:
        annotation = adapter(variant) if adapter else None
        item = dict(variant)
        item["annotation"] = map_annotation(annotation)
        results.append(item)
    return results
