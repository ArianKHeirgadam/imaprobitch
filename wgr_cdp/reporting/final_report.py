"""Final JSON report writer."""

import json
from pathlib import Path


def save_final_report(data, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, indent=2, default=str),
        encoding="utf-8"
    )
    return output
