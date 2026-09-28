"""Candidate discovery and evidence aggregation."""

from .discover import discover_candidates
from .scoring import score_candidate

__all__ = ["discover_candidates", "score_candidate"]
