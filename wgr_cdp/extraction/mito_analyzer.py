from pathlib import Path
import csv
from .schema import FeatureObservation

def parse_mito_table(path,delimiter="\t"):
    with Path(path).open(encoding="utf-8",newline="") as f:
        rows=csv.DictReader(f,delimiter=delimiter); req={"sample_id","position"}
        if not req.issubset(rows.fieldnames or []): raise ValueError(f"mitochondrial table requires {sorted(req)}")
        out=[]
        for r in rows:
            h=r.get("heteroplasmy"); c=r.get("copy_number"); v=h if h not in {None,"","."} else c
            if v in {None,"","."}: out.append(FeatureObservation(f"MT:{r[position]}",r["sample_id"],"MITOCHONDRIAL",None,"Data unavailable",str(path)))
            else: out.append(FeatureObservation(f"MT:{r['position']}",r["sample_id"],"MITOCHONDRIAL",float(v),"Detected",str(path),heteroplasmy=float(h) if h not in {None,"","."} else None,copy_number=float(c) if c not in {None,"","."} else None))
        return out
