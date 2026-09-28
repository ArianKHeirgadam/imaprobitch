"""dbSNP integration for WGR-CDP."""

from .adapter import dbsnp_adapter
from .client import DbSnpClient

__all__ = ["DbSnpClient", "dbsnp_adapter"]
