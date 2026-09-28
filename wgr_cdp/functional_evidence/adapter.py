"""Functional evidence adapter factories."""

from .client import VepClient


def vep_adapter(client=None):
    """Return a VEP callable compatible with the evidence pipeline."""
    client = client or VepClient()
    return client.annotate_variant
