from pathlib import Path
from .manifest import DatasetManifest

def discover_dataset(path):
    path = Path(path)
    samples = []

    for group in ["cancer", "healthy"]:
        folder = path / group
        if not folder.exists():
            continue

        for file in folder.iterdir():
            if file.suffix.lower() in [".vcf", ".csv"]:
                samples.append({
                    "id": file.stem,
                    "group": group,
                    "file": str(file)
                })

    return samples

def load_dataset(path):
    path = Path(path)

    if path.suffix in [".yaml", ".yml"]:
        return DatasetManifest(path)

    return discover_dataset(path)
