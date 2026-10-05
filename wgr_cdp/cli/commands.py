"""Command implementations for WGR-CDP."""
import csv
import json
from pathlib import Path
from wgr_cdp.tracking.run import create_run_record
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

def run_command(healthy,cancer,output,annotate=False,alpha=0.05,timeout=10,features=None,metadata=None,max_panel_size=15,depth=300,error_rate=0.001,cnv=None,literature_search=False,validation_candidates=None,bootstrap=200,background=None,max_background=1.0,cohort_metadata=None):
    run_config = {
        "healthy": str(healthy), "cancer": str(cancer), "alpha": alpha,
        "timeout": timeout, "features": str(features) if features else None,
        "cnv": str(cnv) if cnv else None, "max_panel_size": max_panel_size,
        "depth": depth, "error_rate": error_rate,
        "literature_search": literature_search,
        "validation_candidates": str(validation_candidates) if validation_candidates else None,
        "bootstrap": bootstrap, "background": str(background) if background else None,
        "max_background": max_background,
        "cohort_metadata": str(cohort_metadata) if cohort_metadata else None,
        "robustness_seed": 42,
        "robustness_missingness_repeats": 10,
    }
    run_record = create_run_record(run_config)
    result=analyze_cohorts(healthy,cancer,output,annotate=annotate,alpha=alpha,timeout=timeout)
    result["run"] = run_record

    # C-12 cohort design audit: metadata are optional and never guessed.
    from wgr_cdp.research.cohort_design import merge_design_metadata, validate_cohort_design
    cohort_payload = json.loads((Path(output) / "variants" / "run.json").read_text(encoding="utf-8"))
    cohort_samples = cohort_payload.get("samples", [])
    cohort_metadata_rows = []
    if cohort_metadata:
        with Path(cohort_metadata).open(encoding="utf-8-sig", newline="") as handle:
            cohort_metadata_rows = list(csv.DictReader(handle))
    cohort_samples = merge_design_metadata(cohort_samples, cohort_metadata_rows)
    cohort_audit = validate_cohort_design(cohort_samples)
    cohort_audit["metadata_source"] = str(cohort_metadata) if cohort_metadata else "Data unavailable"
    (Path(output) / "c12_cohort_design.json").write_text(
        json.dumps(cohort_audit, indent=2, default=str), encoding="utf-8"
    )
    result["c12_cohort_design"] = cohort_audit
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
    validation_rows = None
    if validation_candidates:
        with Path(validation_candidates).open(encoding="utf-8-sig", newline="") as h:
            validation_rows = list(csv.DictReader(h))
    result["a6"] = run_a6(
        a5_candidates, DEFAULT_WEIGHTS,
        constraints={"min_detectability":0.0,"max_background":max_background},
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
        constraints={"min_detectability":0.0,"max_background":max_background},
        min_gain=0.02,
        bootstrap=200,
        candidate_layers=candidate_layers,
        presence_matrix=presence_matrix,
    )
    from wgr_cdp.research.a7_final_panel import append_a7_to_report
    append_a7_to_report(output, result["a7"])

    from wgr_cdp.research.validation_coverage import build_presence_matrix_from_rows, compare_frozen_panel_coverage
    validation_presence = None
    if validation_rows:
        validation_presence_payload = build_presence_matrix_from_rows(validation_rows)
        validation_presence = validation_presence_payload.get("matrix")
    selected_a7 = result["a7"].get("panel", {}).get("selected", [])
    validation_coverage = compare_frozen_panel_coverage(
        presence_matrix, validation_presence, selected_a7
    )
    (Path(output) / "c12_validation_coverage.json").write_text(
        json.dumps(validation_coverage, indent=2, default=str), encoding="utf-8"
    )
    result["c12_validation_coverage"] = validation_coverage

    from wgr_cdp.research.a8_validation import run_a8, write_a8_artifacts, append_a8_to_report
    result["a8"] = run_a8(
        selected_a7,
        discovery_rows=a5_candidates,
        validation_rows=validation_rows,
        n_bootstrap=bootstrap,
    )
    write_a8_artifacts(output, result["a8"])
    append_a8_to_report(output, result["a8"])

    from wgr_cdp.research.robustness import write_c09_artifacts, append_c09_to_report
    result["c09"] = write_c09_artifacts(
        output,
        a5_candidates,
        base_weights=DEFAULT_WEIGHTS,
        constraints={"min_detectability": 0.0, "max_background": max_background},
        matrix=matrix,
        k_values=tuple(range(1, min(15, int(max_panel_size)) + 1)),
        missingness_repeats=10,
        min_gain=0.02,
        seed=42,
        k=min(15, int(max_panel_size)),
    )
    append_c09_to_report(output, result["c09"])

    with (Path(output) / "a6_ablation.csv").open("w", encoding="utf-8", newline="") as h:
        fields=["ablation","k","coverage","ineligible","unscored"]
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(result["a6"]["ablations"])

    from wgr_cdp.research.c11_integration import write_c11_artifacts, append_c11_to_report
    result["c11"] = write_c11_artifacts(
        output,
        config=run_config,
        run_id=run_record["run_id"],
    )
    append_c11_to_report(output, result["c11"])

    # A9 is the final provenance layer: hash the completed run artifacts after
    # A8 has finished. The manifest excludes itself to remain self-consistent.
    from wgr_cdp.release.reproducibility import write_reproducibility_manifest
    run_id = run_record["run_id"]
    result["a9"] = {
        "reproducibility_manifest": str(
            write_reproducibility_manifest(
                output,
                config=run_config,
                run_id=run_id,
            )
        )
    }
    return result

def intake_command(project="TCGA-STAD", output="results/intake", file_access=None):
    from wgr_cdp.data_ingestion.gdc import (
        fetch_project, query_files, build_intake_record, write_intake_record,
    )
    project_record = fetch_project(project)
    file_payload = query_files(project, access=file_access) if file_access else None
    record = build_intake_record(project_record, file_payload)
    path = write_intake_record(output, record)
    record["output"] = str(path)
    return record

def validate_command():
    return run_health_check()

def report_command(output):
    path=Path(output)/"report.html"
    if not path.exists(): raise FileNotFoundError(f"report not found: {path}")
    print(path.resolve()); return {"report":str(path.resolve())}


def inventory_command(project="TCGA-STAD", output="results/tcga_stad_inventory", access=None,
                       category=None, strategy=None, data_format=None, modalities=None, max_files=None):
    from wgr_cdp.data_ingestion.gdc_acquisition import (
        inventory_files, build_acquisition_manifest,
        write_acquisition_manifest, write_tsv_manifest,
    )
    rows = inventory_files(
        project, data_category=category, access=access,
        experimental_strategy=strategy, data_format=data_format, max_files=max_files,
    )
    selected = set(modalities) if modalities else None
    manifest = build_acquisition_manifest(project, rows, selected)
    json_path = write_acquisition_manifest(str(output) + ".json", manifest)
    tsv_path = write_tsv_manifest(str(output) + ".tsv", manifest)
    manifest["output_json"] = str(json_path)
    manifest["output_tsv"] = str(tsv_path)
    return manifest

def acquire_command(manifest_path, output_dir, token=None, limit=None):
    from wgr_cdp.data_ingestion.gdc_acquisition import acquire_manifest, write_acquisition_manifest
    path = Path(manifest_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    result = acquire_manifest(manifest, output_dir, token=token, limit=limit)
    write_acquisition_manifest(path, result)
    return result

def cohort_command(project="TCGA-STAD", output="results/tcga_stad_cohort.json", access=None, timeout=30):
    from wgr_cdp.data_ingestion.gdc_cohort import query_cases, query_variant_files, build_cohort_manifest, write_cohort_manifest
    cases = query_cases(project, timeout=timeout)
    files = query_variant_files(project, access=access, timeout=timeout)
    manifest = build_cohort_manifest(project, cases, files)
    path = write_cohort_manifest(output, manifest)
    manifest["output"] = str(path)
    return manifest

def register_command(manifest_path, root, output):
    from wgr_cdp.data_ingestion.gdc_acquisition import register_dataset, write_registration
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    result = register_dataset(manifest, root)
    result["output"] = str(write_registration(output, result))
    return result
