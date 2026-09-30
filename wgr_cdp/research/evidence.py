"""Transparent candidate evidence and hard-constraint filtering."""
from __future__ import annotations
EVIDENCE_FIELDS = ("biological_evidence","statistical_strength","detectability","blood_background_safety","early_stage_score","specificity_score","literature_novelty","literature_validation_gap","literature_diagnostic_utility")
def _score(value):
    if value is None or value == "Data unavailable": return None
    try: value=float(value)
    except (TypeError,ValueError): return None
    return max(0.0,min(1.0,value))
def normalize_evidence(candidate):
    row=dict(candidate or {}); literature=row.get("literature") or {}
    aliases={"literature_novelty":literature.get("novelty",row.get("literature_novelty")),"literature_validation_gap":literature.get("validation_gap",row.get("literature_validation_gap")),"literature_diagnostic_utility":literature.get("diagnostic_utility",row.get("literature_diagnostic_utility"))}
    for key in EVIDENCE_FIELDS:
        value=aliases.get(key,row.get(key)); row[key]=_score(value) if value is not None else "Data unavailable"
    return row
def apply_constraints(candidate,min_detectability=0.0,max_background=1.0,require_assay=True,require_fpr=True):
    row=normalize_evidence(candidate); constraints=dict(row.get("constraints") or {})
    detectability=_score(row.get("detectability")); background=_score(row.get("blood_background_safety"))
    detectable=(not require_assay) if detectability is None else detectability>=float(min_detectability)
    background_safe=True if background is None else background>=max(0.0,1.0-float(max_background))
    assay_ok=bool(constraints.get("assay_ok",True)) if require_assay else True
    fpr_ok=bool(constraints.get("fpr_ok",True)) if require_fpr else True
    row["constraints"]={**constraints,"detectable":detectable,"background_safe":background_safe,"assay_ok":assay_ok,"fpr_ok":fpr_ok,"eligible":bool(detectable and background_safe and assay_ok and fpr_ok)}
    return row
def evidence_vector(candidate):
    row=normalize_evidence(candidate); return {key:row[key] for key in EVIDENCE_FIELDS}
def transparent_weighted_score(candidate,weights):
    row=normalize_evidence(candidate)
    usable={k:_score(row.get(k)) for k in EVIDENCE_FIELDS if _score(row.get(k)) is not None and float(weights.get(k,0))>0}
    total_weight=sum(float(weights.get(k,0)) for k in usable)
    if total_weight<=0: return {"score":None,"status":"Data unavailable","used_fields":[]}
    score=sum(usable[k]*float(weights.get(k,0)) for k in usable)/total_weight
    return {"score":score,"status":"Available","used_fields":sorted(usable)}
def rank_candidates(candidates,weights,constraints=None):
    constraints=dict(constraints or {}); evaluated=[]
    for candidate in candidates:
        row=apply_constraints(candidate,**constraints); scoring=transparent_weighted_score(row,weights)
        row["research_score"]=scoring["score"]; row["score_status"]=scoring["status"]; row["score_fields"]=scoring["used_fields"]; evaluated.append(row)
    eligible=[r for r in evaluated if r["constraints"]["eligible"]]; scored=[r for r in eligible if r["research_score"] is not None]
    scored.sort(key=lambda r:(-r["research_score"],str(r.get("candidate_id",r.get("candidate","")))))
    return {"ranked":scored,"ineligible":[r for r in evaluated if not r["constraints"]["eligible"]],"unscored":[r for r in evaluated if r["research_score"] is None]}
