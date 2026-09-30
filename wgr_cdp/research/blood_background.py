"""Explicit blood-background estimation and filtering."""
from collections import defaultdict

def estimate_background(rows,key="region"):
    groups=defaultdict(list)
    for r in rows:
        try: groups[str(r[key])].append(float(r.get("blood_background",0)))
        except (TypeError,ValueError): pass
    return {k:{"n":len(v),"mean":sum(v)/len(v) if v else None,"max":max(v) if v else None,"source":"observed"} for k,v in groups.items()}

def filter_candidates(candidates,background,max_background=.10):
    kept=[]; rejected=[]
    for row in candidates:
        key=str(row.get("region") or row.get("feature")); bg=background.get(key,{}).get("max")
        x=dict(row); x["blood_background_status"]="Data unavailable" if bg is None else ("pass" if bg<=max_background else "fail")
        (kept if bg is None or bg<=max_background else rejected).append(x)
    return kept,rejected