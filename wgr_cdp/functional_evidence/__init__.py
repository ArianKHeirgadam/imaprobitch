"""Functional evidence layer for WGR-CDP."""

from .adapter import vep_adapter
from .client import VepClient
from .mapper import map_functional_evidence
from .pipeline import add_functional_evidence

__all__ = [
    "VepClient",
    "vep_adapter",
    "map_functional_evidence",
    "add_functional_evidence",
]
