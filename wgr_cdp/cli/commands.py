"""Command implementations for WGR-CDP."""

import csv
from pathlib import Path
from wgr_cdp.application.analysis import analyze_cohorts
from wgr_cdp.release.health import run_health_check


def _metadata(path):
    if not path: return {}
    with open(path,"r",encoding="utf-8-sig",newline="") as h:
        rows=csv.DictReader(h)
        return {r["patient"]:r for r in rows}


def run_command(healthy, cancer, output, annotate=False, alpha=0.05, timeout=10, features=None, metadata=None, max_panel_size=15, depth=300, error_rate=0.001):
    result=analyze_cohorts(healthy,cancer,output,annotate=annotate,alpha=alpha,timeout=timeout)
    if features:
        from wgr_cdp.multimodal.engine import run_multimodal_analysis
        multimodal=run_multimodal_analysis(features,Path(output)/"multimodal",_metadata(metadata),max_panel_size,depth,error_rate)
        result["multimodal"]=multimodal
    return result


def validate_command():
    return run_health_check()


def report_command(output):
    path=Path(output)/"report.html"
    if not path.exists(): raise FileNotFoundError(f"report not found: {path}")
    print(path.resolve()); return {"report":str(path.resolve())}
