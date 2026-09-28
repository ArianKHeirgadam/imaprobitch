"""Attach functional evidence without changing the input variant."""


from .mapper import map_functional_evidence


def add_functional_evidence(variants, adapter):
    """Add normalized functional evidence to each variant."""
    results = []

    for variant in variants:
        evidence = adapter(variant) if adapter else None
        item = dict(variant)
        item["functional_evidence"] = map_functional_evidence(evidence)
        results.append(item)

    return results
