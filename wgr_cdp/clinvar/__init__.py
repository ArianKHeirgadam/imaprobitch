"""ClinVar integration for WGR-CDP."""

from .adapter import clinvar_adapter
from .client import ClinVarClient

__all__ = ["ClinVarClient", "clinvar_adapter"]
