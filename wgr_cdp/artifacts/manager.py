"""Artifact management layer."""

import json
from pathlib import Path


def save_artifact(data, path):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return output


def load_artifact(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)
