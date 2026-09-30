"""Integration helpers for candidate evidence."""
from __future__ import annotations
from .evidence import apply_constraints,transparent_weighted_score
def build_candidate_evidence(candidate,literature=None,stage=None,specificity=None):
    row=dict(candidate or {})
    if literature is not None: row["literature"]=dict(literature)
    if stage is not None: row["early_stage_score"]=stage
    if specificity is not None: row["specificity_score"]=specificity
    return row
def evaluate_candidates(candidates,weights,constraints=None):
    rows=[]
    for candidate in candidates:
        row=apply_constraints(candidate,**dict(constraints or {})); scoring=transparent_weighted_score(row,weights)
        row["research_score"]=scoring["score"]; row["score_status"]=scoring["status"]; row["score_fields"]=scoring["used_fields"]; rows.append(row)
    return rows
