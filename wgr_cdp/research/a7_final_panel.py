"""Phase A7: multimodal evidence integration and final panel design."""
from __future__ import annotations
import csv, json
from pathlib import Path
from .evidence import rank_candidates
from .panel_optimizer import greedy_panel, ilp_panel, alpha_budget, panel_coverage

def load_multimodal_evidence(path):
    path=Path(path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig",newline="") as h:
        return list(csv.DictReader(h))

def _f(value):
    try: return float(value)
    except (TypeError,ValueError): return None

def multimodal_to_candidates(rows):
    out=[]
    for row in rows:
        feature=row.get("feature")
        if not feature:
            continue
        diff=_f(row.get("frequency_difference"))
        detect=_f(row.get("detectability"))
        bg=_f(row.get("blood_background"))
        early=_f(row.get("early_stage_fraction"))
        specificity=_f(row.get("specificity"))
        out.append({
            "candidate_id":str(feature),
            "feature":str(feature),
            "gene":row.get("gene") or "",
            "candidate_type":row.get("feature_type") or "",
            "biological_evidence":"Data unavailable",
            "statistical_strength":"Data unavailable",
            "detectability":detect if detect is not None else "Data unavailable",
            "blood_background_safety":(max(0.0,min(1.0,1.0-bg)) if bg is not None else "Data unavailable"),
            "early_stage_score":early if early is not None else "Data unavailable",
            "specificity_score":specificity if specificity is not None else "Data unavailable",
            "literature_novelty":"Data unavailable",
            "literature_validation_gap":"Data unavailable",
            "literature_diagnostic_utility":"Data unavailable",
            "frequency_difference":diff,
            "validation_status":row.get("validation_status") or "Data unavailable",
        })
    return out

def build_final_panel(candidates, matrix=None, max_k=15, fpr_target=0.05,
                      weights=None, constraints=None):
    weights=weights or {
        "biological_evidence":1.0,"statistical_strength":1.0,"detectability":1.0,
        "blood_background_safety":1.0,"early_stage_score":1.0,
        "specificity_score":1.0,"literature_novelty":1.0,
        "literature_validation_gap":1.0,"literature_diagnostic_utility":1.0,
    }
    constraints=dict(constraints or {"min_detectability":0.0,"max_background":1.0})
    ranking=rank_candidates(candidates,weights,constraints)
    ranked=ranking["ranked"][:int(max_k)]
    ids=[str(x.get("candidate_id") or x.get("feature")) for x in ranked]
    optimization={"status":"Data unavailable","method":"not_run","selected":ids,"coverage":"Data unavailable","k":len(ids)}
    if matrix:
        restricted={p:{c:row.get(c,0) for c in ids if c in row} for p,row in matrix.items()}
        if any(restricted.values()):
            optimization=greedy_panel(restricted,max_k=int(max_k),min_gain=0)
            optimization["status"]="Available"
            optimization["alpha_per_feature"]=alpha_budget(fpr_target,max(1,optimization["k"]))
    return {
        "status":"Available" if candidates else "Data unavailable",
        "constraints":constraints,
        "candidate_count":len(candidates),
        "eligible_count":len(ranking["ranked"]),
        "ineligible_count":len(ranking["ineligible"]),
        "unscored_count":len(ranking["unscored"]),
        "ranked_candidates":ids,
        "panel":optimization,
        "fpr_target":float(fpr_target),
    }

def write_final_panel(output_dir, candidates, matrix=None, max_k=15, fpr_target=0.05,
                      weights=None, constraints=None):
    output=Path(output_dir); output.mkdir(parents=True,exist_ok=True)
    result=build_final_panel(candidates,matrix,max_k,fpr_target,weights,constraints)
    (output/"final_panel.json").write_text(json.dumps(result,indent=2,default=str),encoding="utf-8")
    fields=["rank","candidate_id","feature","gene","candidate_type","detectability","blood_background_safety","early_stage_score","specificity_score","research_score","score_status"]
    with (output/"final_panel_candidates.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,extrasaction="ignore"); w.writeheader()
        ranking=rank_candidates(candidates,weights or {},constraints or {"min_detectability":0.0,"max_background":1.0})["ranked"][:int(max_k)]
        for i,row in enumerate(ranking,1):
            x=dict(row); x["rank"]=i; w.writerow(x)
    return result
