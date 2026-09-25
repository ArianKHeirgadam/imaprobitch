from pathlib import Path
import csv
from .schema import FeatureObservation

def parse_repeat_methylation(path,delimiter="\t"):
    with Path(path).open(encoding="utf-8",newline="") as f:
        rows=csv.DictReader(f,delimiter=delimiter); req={"sample_id","repeat_family","beta"}
        if not req.issubset(rows.fieldnames or []): raise ValueError(f"repeat methylation requires {sorted(req)}")
        out=[]
        for r in rows:
            if r["beta"] in {"",".","NA"}: out.append(FeatureObservation(r["repeat_family"],r["sample_id"],"REPEAT_METHYLATION",None,"Data unavailable",str(path)))
            else: out.append(FeatureObservation(r["repeat_family"],r["sample_id"],"REPEAT_METHYLATION",float(r["beta"]),"Detected",str(path),beta=float(r["beta"])))
        return out
