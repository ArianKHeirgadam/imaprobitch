"""WGR-CDP Phase 1 dataset manifest loader."""

from pathlib import Path
import csv

REQUIRED_FIELDS = {
    "dataset_id","source","assay","genome_build","n_tumor",
    "n_normal","stage_available","normal_type","access",
    "license","notes","status"
}

def load_manifest(path):
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def validate_manifest(rows):
    errors = []
    for i, row in enumerate(rows):
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            errors.append(f"row {i}: missing {sorted(missing)}")
        if row.get("status") not in {"usable","partial","unavailable"}:
            errors.append(f"row {i}: invalid status")
    return errors
