from pathlib import Path
import csv
from .schema import FeatureObservation

def parse_cnv_table(path,delimiter="\t"):
    with Path(path).open(encoding="utf-8",newline="") as f:
        rows=csv.DictReader(f,delimiter=delimiter); req={"sample_id","chromosome","start","end"}
        if not req.issubset(rows.fieldnames or []): raise ValueError(f"CNV table requires {sorted(req)}")
        out=[]
        for r in rows:
            raw=r.get("copy_number") or r.get("log2"); region=f"{r['chromosome']}:{r['start']}-{r['end']}"
            if raw in {None,"","."}: out.append(FeatureObservation(region,r["sample_id"],"CNV",None,"Data unavailable",str(path)))
            else: out.append(FeatureObservation(region,r["sample_id"],"CNV",float(raw),"Detected",str(path),copy_number=float(r["copy_number"]) if r.get("copy_number") not in {None,"","."} else None))
        return out

def parse_sv_table(path,delimiter="\t"):
    with Path(path).open(encoding="utf-8",newline="") as f:
        rows=csv.DictReader(f,delimiter=delimiter); req={"sample_id","chromosome","position","svtype"}
        if not req.issubset(rows.fieldnames or []): raise ValueError(f"SV table requires {sorted(req)}")
        return [FeatureObservation(f"{r['chromosome']}:{r['position']}:{r['svtype']}",r["sample_id"],"SV",1.0,"Detected",str(path)) for r in rows]
