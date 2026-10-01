"""Command implementations for WGR-CDP."""
import csv
import json
from pathlib import Path
from wgr_cdp.application.analysis import analyze_cohorts
from wgr_cdp.release.health import run_health_check
from wgr_cdp.cnv_analysis.analysis import analyze_cnv_segments
from wgr_cdp.data_ingestion.cnv import read_cnv_segments

def _metadata(path):
    if not path: return {}
    with open(path,"r",encoding="utf-8-sig",newline="") as h:
        return {r["patient"]:r for r in csv.DictReader(h)}

def _integrate_candidates(output, snv_candidates, cnv_candidates):
    rows=[]
    for row in snv_candidates:
        rows.append({"candidate_type":"SNV_INDEL","feature":row.get("feature"),"gene":row.get("gene"),"event_type":"","frequency_difference":row.get("frequency_difference"),"p_value":row.get("p_value"),"q_value":row.get("q_value"),"score":row.get("evidence_score")})
    for row in cnv_candidates:
        rows.append({"candidate_type":"CNV","feature":row.get("feature"),"gene":"","event_type":row.get("event_type"),"frequency_difference":row.get("frequency_difference"),"p_value":row.get("p_value"),"q_value":row.get("q_value"),"score":row.get("candidate_score")})
    path=Path(output)/"multimodal"; path.mkdir(parents=True,exist_ok=True)
    fields=["candidate_type","feature","gene","event_type","frequency_difference","p_value","q_value","score"]
    with (path/"integrated_candidates.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(rows)

def run_command(healthy,cancer,output,annotate=False,alpha=0.05,timeout=10,features=None,metadata=None,max_panel_size=15,depth=300,error_rate=0.001,cnv=None,literature_search=False,validation_candidates=None,bootstrap=200):
    result=analyze_cohorts(healthy,cancer,output,annotate=annotate,alpha=alpha,timeout=timeout)
    cnv_candidates=[]
    if cnv:
        cnv_rows=read_cnv_segments(cnv)
        result["cnv"]=analyze_cnv_segments(cnv_rows,Path(output)/"cnv",alpha=alpha)
        with (Path(output)/"cnv"/"cnv_candidates.csv").open(encoding="utf-8") as h:
            cnv_candidates=list(csv.DictReader(h))
    if features:
        from wgr_cdp.multimodal.engine import run_multimodal_analysis
        result["multimodal"]=run_multimodal_analysis(features,Path(output)/"multimodal",_metadata(metadata),max_panel_size,depth,error_rate)
    _integrate_candidates(output,result.get("candidates",[]),cnv_candidates)
    from wgr_cdp.research.a5_integration import write_a5_artifacts
    a5_candidates=list(result.get("candidates",[]))
    a5_candidates.extend(cnv_candidates)
    if features:
        from wgr_cdp.research.a7_final_panel import load_multimodal_evidence, multimodal_to_candidates
        mm_rows=load_multimodal_evidence(Path(output)/"multimodal"/"multimodal_cohort_comparison.csv")
        a5_candidates.extend(multimodal_to_candidates(mm_rows))
    result["a5"]=write_a5_artifacts(
        output,
        a5_candidates,
        weights=None,
        constraints={"min_detectability":0.0,"max_background":1.0},
        literature_search=literature_search,
    )
    from wgr_cdp.research.a5_integration import append_a5_to_report
    append_a5_to_report(output, result["a5"])
    from wgr_cdp.research.a6_validation import run_a6
    from wgr_cdp.research.a5_integration import DEFAULT_WEIGHTS
    matrix = None
    matrix_path = Path(output) / "multimodal" / "patient_candidate_matrix.csv"
    if matrix_path.exists():
        matrix = {}
        with matrix_path.open(encoding="utf-8", newline="") as h:
            for row in csv.DictReader(h):
                patient = row.pop("patient")
                matrix[patient] = {}
                for key, value in row.items():
                    try: matrix[patient][key] = float(value)
                    except (TypeError, ValueError): pass
    validation_rows = None
    if validation_candidates:
        with Path(validation_candidates).open(encoding="utf-8-sig", newline="") as h:
            validation_rows = list(csv.DictReader(h))
    result["a6"] = run_a6(
        a5_candidates, DEFAULT_WEIGHTS,
        constraints={"min_detectability":0.0,"max_background":1.0},
        matrix=matrix, k=max_panel_size,
        n_bootstrap=bootstrap, validation_candidates=validation_rows,
    )
    (Path(output) / "a6_validation.json").write_text(
        json.dumps(result["a6"], indent=2, default=str), encoding="utf-8"
    )
    (Path(output) / "a6_baseline_comparison.json").write_text(
        json.dumps(result["a6"]["baseline_comparison"], indent=2, default=str), encoding="utf-8"
    )
    (Path(output) / "a6_bootstrap_stability.json").write_text(
        json.dumps(result["a6"]["bootstrap_stability"], indent=2, default=str), encoding="utf-8"
    )
    from wgr_cdp.research.a7_final_panel import write_final_panel
    candidate_layers = {
        str(row.get("candidate_id") or row.get("feature") or row.get("candidate")):
        str(row.get("candidate_type") or row.get("feature_type") or "Data unavailable")
        for row in a5_candidates
    }
    result["a7"] = write_final_panel(
        output, a5_candidates, matrix=matrix, max_k=min(15, max_panel_size),
        fpr_target=alpha,
        constraints={"min_detectability":0.0,"max_background":1.0},
        min_gain=0.02,
        bootstrap=200,
        candidate_layers=candidate_layers,
    )
    from wgr_cdp.research.a7_final_panel import append_a7_to_report
    append_a7_to_report(output, result["a7"])

    # A8 is intentionally additive: it consumes A7's selected panel and the
    # optional independent validation table without changing A0-A7 behavior.
    from wgr_cdp.research.a8_validation import run_a8, write_a8_artifacts, append_a8_to_report
    selected_a7 = result["a7"].get("panel", {}).get("selected", [])
    result["a8"] = run_a8(
        selected_a7,
        discovery_rows=a5_candidates,
        validation_rows=validation_rows,
        n_bootstrap=bootstrap,
    )
    write_a8_artifacts(output, result["a8"])
    append_a8_to_report(output, result["a8"])

    with (Path(output) / "a6_ablation.csv").open("w", encoding="utf-8", newline="") as h:
        fields=["ablation","k","coverage","ineligible","unscored"]
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(result["a6"]["ablations"])
    return result

def validate_command():
    return run_health_check()

def report_command(output):
    path=Path(output)/"report.html"
    if not path.exists(): raise FileNotFoundError(f"report not found: {path}")
    print(path.resolve()); return {"report":str(path.resolve())}
