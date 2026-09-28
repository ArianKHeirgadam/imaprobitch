"""Adapter factory for the existing WGR-CDP annotation pipeline."""

from .client import ClinVarClient


def clinvar_adapter(client=None):
    """Return an adapter callable compatible with annotate_variants."""
    client = client or ClinVarClient()
    return client.lookup_variant
