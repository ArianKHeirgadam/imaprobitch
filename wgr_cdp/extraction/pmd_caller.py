from pathlib import Path
import csv
from .schema import FeatureObservation

def load_pmd_table(path,delimiter="\t"):
    with Path(path).open(encoding="utf-8",newline="") as f:
        rows=csv.DictReader(f,delimiter=delimiter); req={"sample_id","chromosome","start","end"}
        if not req.issubset(rows.fieldnames or []): raise ValueError(f"PMD table requires {sorted(req)}")
        return [FeatureObservation(f"{r['chromosome']}:{r['start']}-{r['end']}",r["sample_id"],"PMD",1.0,"Detected",str(path)) for r in rows]
