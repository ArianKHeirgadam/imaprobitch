"""Adapter factory for the WGR-CDP annotation pipeline."""

from .client import DbSnpClient


def dbsnp_adapter(client=None):
    """Return an adapter compatible with annotate_variants."""
    client = client or DbSnpClient()
    return client.lookup_variant
