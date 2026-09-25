"""Evidence model for annotation sources."""

from dataclasses import dataclass


@dataclass
class AnnotationEvidence:
    source: str
    variant_id: str
    classification: str | None = None
    description: str | None = None
    confidence: str | None = None
