"""End-to-end real VCF cohort analysis.

This module connects real VCF ingestion to cohort comparison, FDR correction,
optional external annotation, candidate prioritization, and report artifacts.
"""

import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from wgr_cdp.candidate_discovery.discover import discover_candidates
from wgr_cdp.cohort_analysis.compare import compare_gene_cohorts, compare_variant_cohorts
from wgr_cdp.data_ingestion.vcf_cohort import read_vcf_cohort
from wgr_cdp.evaluation.multiple_testing import add_fdr, filter_significant


def _variant_key(record):
    return f"{record['chrom']}:{record['pos']}:{record['ref']}:{record['alt']}"


def _parse_info(info):
    values = {}
    for item in str(info or "").split(";"):
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            values[key.upper()] = value
        else:
            values[item.upper()] = True
    return values


def _record_with_info(record):
    info = _parse_info(record.get("info"))
    return {
        **record,
        "variant_key": _variant_key(record),
        "gene": info.get("GENE") or info.get("GENE_SYMBOL") or info.get("SYMBOL"),
        "consequence": info.get("CONSEQUENCE") or info.get("CSQ_CONSEQUENCE"),
        "impact": info.get("IMPACT") or info.get("CSQ_IMPACT"),
    }


def _load_cohort(directory, group):
    directory = Path(directory)
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"cohort directory does not exist: {directory}")
    paths = sorted(directory.glob("*.vcf")) + sorted(directory.glob("*.vcf.gz"))
    if not paths:
        raise ValueError(f"no .vcf or .vcf.gz files found in: {directory}")
    samples = []
    for path in paths:
        samples.extend(read_vcf_cohort(path, group))
    return samples


def _build_annotations(variant_records, annotate=False, timeout=10):
    annotations = {}
    functional = {}
    if not annotate:
        for key, record in variant_records.items():
            annotation = {}
            functional_record = {
                "gene": record.get("gene"),
                "consequence": record.get("consequence"),
                "impact": record.get("impact"),
            }
            if any(functional_record.values()):
                functional[key] = functional_record
        return annotations, functional

    from wgr_cdp.clinvar.client import ClinVarClient
    from wgr_cdp.dbsnp.client import DbSnpClient
    from wgr_cdp.functional_evidence.client import VepClient

    clinvar = ClinVarClient(timeout=timeout)
    dbsnp = DbSnpClient(timeout=timeout)
    vep = VepClient(timeout=timeout)

    for key, record in variant_records.items():
        try:
            annotations[key] = clinvar.lookup_variant(record)
        except Exception as exc:
            annotations[key] = {"source": "clinvar", "error": str(exc)}
        try:
            annotations[key].update(dbsnp.lookup_variant(record))
        except Exception as exc:
            annotations[key]["dbsnp_error"] = str(exc)
        try:
            functional[key] = vep.annotate_variant(record)
        except Exception as exc:
            functional[key] = {"source": "ensembl_vep", "error": str(exc)}

        local = {
            "gene": record.get("gene"),
            "consequence": record.get("consequence"),
            "impact": record.get("impact"),
        }
        for name, value in local.items():
            if value and not functional[key].get(name):
                functional[key][name] = value
    return annotations, functional


def _write_csv(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in columns})


def _write_html(path, summary, candidates):
    top = candidates[:25]
    rows = []
    for row in top:
        rows.append(
            "<tr>"
            + "".join(
                f"<td>{html.escape(str(row.get(k, '')))}</td>"
                for k in ["candidate_rank", "feature", "case_frequency", "control_frequency", "frequency_difference", "p_value", "q_value", "evidence_score"]
            )
            + "</tr>"
        )
    document = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>WGR-CDP analysis report</title>
<style>body{{font-family:Arial,sans-serif;margin:32px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:6px;text-align:left}}th{{background:#eee}}code{{background:#f5f5f5;padding:2px 4px}}</style></head>
<body><h1>WGR-CDP Research Analysis</h1>
<p>Generated: <code>{html.escape(summary['generated_at'])}</code></p>
<ul><li>Healthy samples: {summary['control_samples']}</li><li>Cancer samples: {summary['case_samples']}</li><li>Unique variants: {summary['unique_variants']}</li><li>FDR-significant variants: {summary['significant_variants']}</li><li>FDR-significant genes: {summary['significant_genes']}</li></ul>
<h2>Top candidates</h2><table><thead><tr><th>Rank</th><th>Variant</th><th>Cancer freq</th><th>Healthy freq</th><th>Difference</th><th>p</th><th>q</th><th>Score</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p><strong>Research use only:</strong> candidate scores are prioritization signals, not clinical probabilities or diagnostic results.</p></body></html>"""
    path.write_text(document, encoding="utf-8")


def analyze_cohorts(healthy_dir, cancer_dir, output_dir, annotate=False, alpha=0.05, timeout=10):
    """Run the real cohort analysis and write machine-readable results."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    controls = _load_cohort(healthy_dir, "control")
    cases = _load_cohort(cancer_dir, "case")
    samples = controls + cases

    variant_results = compare_variant_cohorts(samples)
    variant_results = add_fdr(variant_results)

    variant_records = {}
    for sample in samples:
        for record in sample.get("variant_records", []):
            variant_records.setdefault(record["variant_key"], record)

    annotations, functional = _build_annotations(variant_records, annotate=annotate, timeout=timeout)
    candidates = discover_candidates(variant_results, annotations, functional)
    significant_variants = filter_significant(variant_results, alpha=alpha)

    gene_results = compare_gene_cohorts(samples) if any(s.get("variant_records") for s in samples) else []
    gene_results = add_fdr(gene_results)
    significant_genes = filter_significant(gene_results, alpha=alpha)

    for candidate in candidates:
        candidate["variant_type"] = (variant_records.get(candidate.get("feature")) or {}).get("variant_type")
        candidate["gene"] = (candidate.get("functional_evidence") or {}).get("gene")
        candidate["consequence"] = (candidate.get("functional_evidence") or {}).get("consequence")
        candidate["impact"] = (candidate.get("functional_evidence") or {}).get("impact")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "control_samples": len(controls),
        "case_samples": len(cases),
        "unique_variants": len(variant_results),
        "tested_variants": len(variant_results),
        "significant_variants": len(significant_variants),
        "unique_genes": len(gene_results),
        "significant_genes": len(significant_genes),
        "alpha": float(alpha),
        "external_annotation_enabled": bool(annotate),
        "status": "completed",
    }

    variant_columns = ["feature", "variant_type", "case_carriers", "control_carriers", "case_n", "control_n", "case_frequency", "control_frequency", "frequency_difference", "case_control_frequency_ratio", "p_value", "q_value"]
    gene_columns = variant_columns
    candidate_columns = ["candidate_rank", "feature", "variant_type", "gene", "case_frequency", "control_frequency", "frequency_difference", "p_value", "q_value", "evidence_score", "consequence", "impact"]

    _write_csv(output / "variants.csv", variant_results, variant_columns)
    _write_csv(output / "significant_variants.csv", significant_variants, variant_columns)
    _write_csv(output / "genes.csv", gene_results, gene_columns)
    _write_csv(output / "significant_genes.csv", significant_genes, gene_columns)
    _write_csv(output / "candidates.csv", candidates, candidate_columns)

    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output / "annotations.json").write_text(json.dumps({"annotations": annotations, "functional": functional}, indent=2), encoding="utf-8")
    (output / "run.json").write_text(json.dumps({"summary": summary, "samples": samples}, indent=2), encoding="utf-8")
    _write_html(output / "report.html", summary, candidates)
    return {"summary": summary, "output_dir": str(output), "candidates": candidates}
