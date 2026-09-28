"""Command implementations for WGR-CDP."""
import csv
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

def run_command(healthy,cancer,output,annotate=False,alpha=0.05,timeout=10,features=None,metadata=None,max_panel_size=15,depth=300,error_rate=0.001,cnv=None):
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
    return result

def validate_command():
    return run_health_check()

def report_command(output):
    path=Path(output)/"report.html"
    if not path.exists(): raise FileNotFoundError(f"report not found: {path}")
    print(path.resolve()); return {"report":str(path.resolve())}
