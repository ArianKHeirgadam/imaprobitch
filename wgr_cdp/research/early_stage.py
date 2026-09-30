"""Stage-stratified candidate evidence without inventing missing stages."""
from __future__ import annotations
STAGE_GROUPS={"early":{"I","II","1","2","stage_i","stage_ii"},"late":{"III","IV","3","4","stage_iii","stage_iv"}}
def _stage_group(value):
    key=str(value or "").strip().lower()
    for group,values in STAGE_GROUPS.items():
        if key in {v.lower() for v in values}: return group
    return None
def stage_candidate_rates(rows,candidate_key="candidate",detected_key="detected"):
    groups={"early":{},"late":{}}
    for row in rows:
        group=_stage_group(row.get("stage"))
        if group is None: continue
        candidate=str(row.get(candidate_key,"")); groups[group].setdefault(candidate,[]).append(bool(row.get(detected_key)))
    out={}
    for candidate in sorted(set(groups["early"])|set(groups["late"])):
        early=groups["early"].get(candidate,[]); late=groups["late"].get(candidate,[])
        out[candidate]={"early_rate":sum(early)/len(early) if early else None,"late_rate":sum(late)/len(late) if late else None,"early_n":len(early),"late_n":len(late),"status":"Available" if early or late else "Data unavailable"}
    return out
def early_stage_score(row):
    early=row.get("early_rate")
    return "Data unavailable" if early is None else max(0.0,min(1.0,float(early)))
