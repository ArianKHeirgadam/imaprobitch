from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class Sample:
    sample_id: str
    group: str
    vcf: str | None = None
    cnv: str | None = None

class DatasetManifest:
    def __init__(self, path):
        self.path = Path(path)
        self.project = None
        self.reference = None
        self.samples = []
        self._load()

    def _load(self):
        if not self.path.exists():
            raise FileNotFoundError(f"Dataset manifest not found: {self.path}")

        with self.path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.project = data.get("project", {})
        self.reference = data.get("reference", {})

        for item in data.get("samples", []):
            self.samples.append(
                Sample(
                    sample_id=item["id"],
                    group=item["group"],
                    vcf=item.get("vcf"),
                    cnv=item.get("cnv"),
                )
            )

    def count(self):
        return len(self.samples)

    def groups(self):
        return sorted({s.group.lower() for s in self.samples})
