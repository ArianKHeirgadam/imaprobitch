from pathlib import Path
import csv
from .schema import FeatureObservation

def parse_methylation_table(path,delimiter="\t"):
    with Path(path).open(encoding="utf-8",newline="") as f:
        rows=csv.DictReader(f,delimiter=delimiter); req={"sample_id","region"}
        if not req.issubset(rows.fieldnames or []): raise ValueError(f"methylation table requires {sorted(req)}")
        out=[]
        for r in rows:
            b=r.get("beta"); m=r.get("m_value") or r.get("M")
            if b in {None,"","."} and m in {None,"","."}: out.append(FeatureObservation(r["region"],r["sample_id"],"METHYLATION",None,"Data unavailable",str(path))); continue
            bv=float(b) if b not in {None,"","."} else None; mv=float(m) if m not in {None,"","."} else None
            out.append(FeatureObservation(r["region"],r["sample_id"],"METHYLATION",bv if bv is not None else mv,"Detected",str(path),beta=bv,m_value=mv))
        return out
