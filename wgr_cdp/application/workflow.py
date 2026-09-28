"""WGR-CDP Phase 31 workflow orchestration."""

from pathlib import Path

from wgr_cdp.application.analysis import analyze_cohorts
from wgr_cdp.cnv_analysis.analysis import analyze_cnv_segments
from wgr_cdp.data_ingestion.cnv import read_cnv_segments
from wgr_cdp.tracking.run import create_run_record


def run_research_workflow(healthy_path, cancer_path, output_dir, cnv_path=None):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    result = {
        "run": create_run_record({
            "healthy": str(healthy_path),
            "cancer": str(cancer_path),
            "cnv": str(cnv_path) if cnv_path else None,
        }),
        "analysis": {},
        "cnv": None,
    }

    result["analysis"] = analyze_cohorts(
        healthy_path,
        cancer_path,
        output / "variants"
    )

    if cnv_path:
        result["cnv"] = analyze_cnv_segments(
            read_cnv_segments(cnv_path),
            output / "cnv"
        )

    return result
