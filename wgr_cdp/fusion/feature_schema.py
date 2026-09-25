"""Unified feature schema for multi-omics fusion."""

from dataclasses import dataclass, field


@dataclass
class UnifiedFeatureVector:
    sample_id: str
    features: dict = field(default_factory=dict)

    def add_feature(self, name, value):
        self.features[name] = value
