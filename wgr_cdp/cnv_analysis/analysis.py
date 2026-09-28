"""Real CNV cohort comparison and candidate discovery."""
import csv
from pathlib import Path
from wgr_cdp.cohort_analysis.statistics import fisher_exact_2x2
from wgr_cdp.evaluation.multiple_testing import add_fdr, filter_significant

def _write_csv(path, rows, fields):
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def _event_key(row):
    return f"{row['chrom']}:{row['start']}-{row['end']}|{row['event_type']}"

def _gene_events(rows):
    out = []
    for row in rows:
        if row["event_type"] not in {"GAIN", "LOSS"} or not row.get("genes"):
            continue
        for gene in [g.strip() for g in str(row["genes"]).replace(";", ",").split(",") if g.strip()]:
            out.append({**row, "gene": gene})
    return out

def _compare(rows, key_name="region"):
    cases = sorted({r["sample_id"] for r in rows if str(r.get("group", "")).lower() in {"case", "cancer", "tumor"}})
    controls = sorted({r["sample_id"] for r in rows if str(r.get("group", "")).lower() in {"control", "healthy", "normal"}})
    if not cases or not controls:
        raise ValueError("CNV cohort comparison requires both Cancer and Healthy samples")
    def key(r):
        return _event_key(r) if key_name == "region" else f"{r[key_name]}|{r['event_type']}"
    results = []
    for feature in sorted({key(r) for r in rows if r["event_type"] in {"GAIN", "LOSS"}}):
        present = [r for r in rows if key(r) == feature]
        case_carriers = {r["sample_id"] for r in present if r["sample_id"] in cases}
        control_carriers = {r["sample_id"] for r in present if r["sample_id"] in controls}
        a, b = len(case_carriers), len(control_carriers)
        c, d = len(cases)-a, len(controls)-b
        cf, hf = a/len(cases), b/len(controls)
        results.append({
            "feature": feature, "event_type": present[0]["event_type"],
            "case_carriers": a, "control_carriers": b,
            "case_n": len(cases), "control_n": len(controls),
            "case_frequency": cf, "control_frequency": hf,
            "frequency_difference": cf-hf, "effect_size": abs(cf-hf),
            "p_value": fisher_exact_2x2(a,b,c,d),
        })
    return add_fdr(results)

def _score(row):
    score = min(60.0, abs(float(row["frequency_difference"])) * 60.0)
    q = float(row.get("q_value", 1.0))
    if q <= 0.01: score += 30.0
    elif q <= 0.05: score += 15.0
    return round(min(100.0, score), 6)

def analyze_cnv_segments(rows, output_dir, alpha=0.05):
    if not rows:
        raise ValueError("no CNV segments supplied")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    normalized_fields = ["sample_id","group","stage","chrom","start","end","region","copy_number","log2_ratio","event_type","genes","feature_type","status"]
    _write_csv(output/"cnv_segments.csv", rows, normalized_fields)
    gene_rows = _gene_events(rows)
    gene_input = [{"sample_id":r["sample_id"],"group":r["group"],"event_type":r["event_type"],"gene":r["gene"]} for r in gene_rows]
    gene_comparison = _compare(gene_input, "gene") if gene_input else []
    region_comparison = _compare(rows, "region")
    significant = filter_significant(region_comparison, alpha=alpha)
    candidates = []
    for row in significant:
        candidates.append({**row, "candidate_type":"CNV", "candidate_score":_score(row)})
    candidates.sort(key=lambda x:(-x["candidate_score"], x["q_value"], x["feature"]))
    for i,row in enumerate(candidates,1): row["candidate_rank"] = i
    _write_csv(output/"cnv_gene_events.csv", gene_rows, ["sample_id","group","stage","gene","event_type","region","log2_ratio","copy_number","status"])
    comparison_fields = ["feature","event_type","case_carriers","control_carriers","case_n","control_n","case_frequency","control_frequency","frequency_difference","effect_size","p_value","q_value"]
    _write_csv(output/"cnv_region_comparison.csv", region_comparison, comparison_fields)
    _write_csv(output/"significant_cnvs.csv", significant, comparison_fields)
    _write_csv(output/"cnv_candidates.csv", candidates, ["candidate_rank","candidate_type","feature","event_type","case_carriers","control_carriers","case_frequency","control_frequency","frequency_difference","effect_size","p_value","q_value","candidate_score"])
    return {"segments":len(rows),"gene_events":len(gene_rows),"gene_tests":len(gene_comparison),"regions_tested":len(region_comparison),"significant_cnvs":len(significant),"candidates":len(candidates)}
