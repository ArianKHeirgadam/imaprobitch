"""Differential specificity evidence against supplied comparator groups."""
from __future__ import annotations
def specificity_rates(rows,candidate_key="candidate",detected_key="detected",group_key="group"):
    grouped={}
    for row in rows:
        candidate=str(row.get(candidate_key,"")); group=str(row.get(group_key,"")).strip().lower()
        grouped.setdefault(candidate,{}).setdefault(group,[]).append(bool(row.get(detected_key)))
    return {c:{g:{"rate":sum(v)/len(v) if v else None,"n":len(v)} for g,v in groups.items()} for c,groups in grouped.items()}
def specificity_score(candidate_rates,target_groups=("healthy",),competing_groups=()):
    target=[candidate_rates[g]["rate"] for g in target_groups if g in candidate_rates and candidate_rates[g]["rate"] is not None]
    competing=[candidate_rates[g]["rate"] for g in competing_groups if g in candidate_rates and candidate_rates[g]["rate"] is not None]
    if not target: return "Data unavailable"
    target_rate=sum(target)/len(target)
    if not competing: return max(0.0,min(1.0,1.0-target_rate))
    return max(0.0,min(1.0,1.0-max(target_rate,sum(competing)/len(competing))))
