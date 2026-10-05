"""Real CNV cohort comparison and candidate discovery."""

import csv
from pathlib import Path

from wgr_cdp.cohort_analysis.statistics import fisher_exact_2x2
from wgr_cdp.evaluation.multiple_testing import add_fdr, filter_significant
from wgr_cdp.research.cnv_statistics import describe_cnv_statistics
from wgr_cdp.research.statistics import benjamini_hochberg


def _write_csv(path, rows, fields):
    with Path(path).open(
        "w",
        encoding="utf-8",
        newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def _event_key(row):
    return f"{row['chrom']}:{row['start']}-{row['end']}|{row['event_type']}"


def _gene_events(rows):
    out = []

    for row in rows:

        genes = row.get("genes") or row.get("gene")

        if not genes:
            continue


        for gene in str(genes).replace(
            ";",
            ","
        ).split(","):

            gene = gene.strip()

            if not gene:
                continue


            out.append(
                {
                    **row,
                    "gene": gene
                }
            )

    return out


def _compare(rows, key_name="region"):
    """Compare CNV events using explicit observations only.

    A missing segment is not interpreted as a neutral CNV call. A sample is
    included in a denominator only when the relevant region has an explicit
    CNV observation (GAIN, LOSS, or NEUTRAL). Data-unavailable observations
    are excluded from both carrier and denominator counts.
    """
    case_samples = {
        r["sample_id"] for r in rows
        if str(r.get("group", "")).lower() in {"case", "cancer", "tumor"}
    }
    control_samples = {
        r["sample_id"] for r in rows
        if str(r.get("group", "")).lower() in {"control", "healthy", "normal"}
    }
    if not case_samples or not control_samples:
        raise ValueError("CNV cohort comparison requires both Cancer and Healthy samples")

    def region_key(row):
        return f"{row['chrom']}:{row['start']}-{row['end']}"

    def key(row):
        base = row.get("gene") if key_name == "gene" else region_key(row)
        return f"{base}|{row['event_type']}"

    def observed(row):
        return row.get("event_type") in {"GAIN", "LOSS", "NEUTRAL"}

    features = sorted({
        key(r) for r in rows
        if r.get("event_type") in {"GAIN", "LOSS"}
    })
    results = []

    for feature in features:
        event = feature.rsplit("|", 1)[1]
        present = [r for r in rows if key(r) == feature]
        if key_name == "region":
            base = feature.rsplit("|", 1)[0]
            region_rows = [r for r in rows if region_key(r) == base and observed(r)]
        else:
            base = feature.rsplit("|", 1)[0]
            region_rows = [r for r in rows if str(r.get("gene", "")) == base and observed(r)]

        case_observed = {r["sample_id"] for r in region_rows if r["sample_id"] in case_samples}
        control_observed = {r["sample_id"] for r in region_rows if r["sample_id"] in control_samples}
        case_carriers = {r["sample_id"] for r in present if r["sample_id"] in case_samples}
        control_carriers = {r["sample_id"] for r in present if r["sample_id"] in control_samples}

        a = len(case_carriers & case_observed)
        b = len(control_carriers & control_observed)
        case_n = len(case_observed)
        control_n = len(control_observed)
        c_count = case_n - a
        d_count = control_n - b

        case_frequency = a / case_n if case_n else None
        control_frequency = b / control_n if control_n else None
        frequency_difference = (
            case_frequency - control_frequency
            if case_frequency is not None and control_frequency is not None else None
        )

        value_rows = [r for r in region_rows if r.get("event_type") == event]
        numeric_values = []
        for row in value_rows:
            raw = row.get("log2_ratio")
            if raw in (None, ""):
                raw = row.get("segment_mean")
            try:
                if raw not in (None, ""):
                    numeric_values.append(float(raw))
            except (TypeError, ValueError):
                pass

        case_values = [
            float(r.get("log2_ratio") if r.get("log2_ratio") not in (None, "") else r.get("segment_mean"))
            for r in value_rows
            if r["sample_id"] in case_samples
            and (r.get("log2_ratio") not in (None, "") or r.get("segment_mean") not in (None, ""))
        ]
        control_values = [
            float(r.get("log2_ratio") if r.get("log2_ratio") not in (None, "") else r.get("segment_mean"))
            for r in value_rows
            if r["sample_id"] in control_samples
            and (r.get("log2_ratio") not in (None, "") or r.get("segment_mean") not in (None, ""))
        ]

        dosage_stats = describe_cnv_statistics(case_values, control_values, permutations=999, seed=42)
        results.append({
            "feature": feature,
            "event_type": event,
            "statistical_method": "Fisher exact test on explicit event carrier status",
            "dosage_statistical_method": dosage_stats["statistical_test"],
            "case_carriers": a,
            "control_carriers": b,
            "case_n": case_n,
            "control_n": control_n,
            "case_observed": case_n,
            "control_observed": control_n,
            "case_frequency": case_frequency,
            "control_frequency": control_frequency,
            "frequency_difference": frequency_difference,
            "effect_size": abs(frequency_difference) if frequency_difference is not None else None,
            "direction": (
                "case_enriched" if frequency_difference is not None and frequency_difference > 0
                else "control_enriched" if frequency_difference is not None and frequency_difference < 0
                else "balanced" if frequency_difference is not None else "Data unavailable"
            ),
            "case_mean_log2": sum(case_values) / len(case_values) if case_values else None,
            "control_mean_log2": sum(control_values) / len(control_values) if control_values else None,
            "dosage_mean_difference": dosage_stats["mean_difference"],
            "dosage_effect_size": dosage_stats["effect_size"],
            "dosage_p_value": dosage_stats["p_value"],
            "p_value": fisher_exact_2x2(a, b, c_count, d_count) if case_n and control_n else 1.0,
        })

    results = add_fdr(results)
    dosage_p = [row["dosage_p_value"] for row in results if row.get("dosage_p_value") is not None]
    dosage_q = benjamini_hochberg(dosage_p) if dosage_p else []
    index = 0
    for row in results:
        if row.get("dosage_p_value") is not None:
            row["dosage_q_value"] = dosage_q[index]
            index += 1
        else:
            row["dosage_q_value"] = None
    return results

def _score(row):

    score = min(
        60.0,
        abs(
            float(
                row["frequency_difference"]
            )
        )*60
    )


    q=float(
        row.get(
            "q_value",
            1
        )
    )


    if q <=0.01:
        score+=30

    elif q<=0.05:
        score+=15


    return round(
        min(
            100,
            score
        ),
        6
    )



def analyze_cnv_segments(
    rows,
    output_dir,
    alpha=0.05
):

    if not rows:
        raise ValueError(
            "no CNV segments supplied"
        )


    output=Path(output_dir)
    output.mkdir(
        parents=True,
        exist_ok=True
    )


    _write_csv(
        output/"cnv_segments.csv",
        rows,
        list(rows[0].keys())
    )


    gene_rows=_gene_events(rows)


    gene_comparison=[]


    if gene_rows:

        gene_comparison=_compare(
            gene_rows,
            "gene"
        )


    region_comparison=_compare(
        rows,
        "region"
    )


    _write_csv(
        output/"cnv_region_comparison.csv",
        region_comparison,
        list(region_comparison[0].keys()) if region_comparison else []
    )

    if gene_comparison:
        _write_csv(
            output/"cnv_gene_comparison.csv",
            gene_comparison,
            list(gene_comparison[0].keys())
        )

    significant=filter_significant(
        region_comparison,
        alpha=alpha
    )


    _write_csv(
        output/"significant_cnvs.csv",
        significant,
        list(significant[0].keys()) if significant else [
            "feature", "event_type", "case_carriers", "control_carriers",
            "case_n", "control_n", "case_observed", "control_observed",
            "case_frequency", "control_frequency", "frequency_difference",
            "effect_size", "direction", "case_mean_log2", "control_mean_log2",
            "dosage_mean_difference", "dosage_effect_size", "dosage_p_value",
            "dosage_q_value", "statistical_method", "dosage_statistical_method",
            "p_value", "q_value"
        ]
    )


    candidates=[]


    for row in significant:

        candidates.append(
            {
                **row,
                "candidate_type":"CNV",
                "candidate_score":_score(row)
            }
        )


    candidates.sort(
        key=lambda x:
        (
            -x["candidate_score"],
            x["q_value"],
            x["feature"]
        )
    )


    for i,row in enumerate(
        candidates,
        1
    ):
        row["candidate_rank"]=i



    _write_csv(
        output/"cnv_candidates.csv",
        candidates,
        list(candidates[0].keys()) if candidates else [
            "feature", "event_type", "case_carriers", "control_carriers",
            "case_n", "control_n", "case_observed", "control_observed",
            "case_frequency", "control_frequency", "frequency_difference",
            "effect_size", "direction", "case_mean_log2", "control_mean_log2",
            "p_value", "q_value", "candidate_type", "candidate_score", "candidate_rank"
        ]
    )

    _write_csv(
        output/"cnv_gene_events.csv",
        gene_rows,
        list(gene_rows[0].keys())
        if gene_rows else []
    )


    return {
        "segments":len(rows),
        "gene_events":len(gene_rows),
        "gene_tests":len(gene_comparison),
        "regions_tested":len(region_comparison),
        "significant_cnvs":len(significant),
        "candidates":len(candidates)
    }