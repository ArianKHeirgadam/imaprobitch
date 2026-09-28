"""Real CNV cohort comparison and candidate discovery."""

import csv
from pathlib import Path

from wgr_cdp.cohort_analysis.statistics import fisher_exact_2x2
from wgr_cdp.evaluation.multiple_testing import add_fdr, filter_significant


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

    cases = sorted(
        {
            r["sample_id"]
            for r in rows
            if str(
                r.get("group","")
            ).lower()
            in {
                "case",
                "cancer",
                "tumor"
            }
        }
    )


    controls = sorted(
        {
            r["sample_id"]
            for r in rows
            if str(
                r.get("group","")
            ).lower()
            in {
                "control",
                "healthy",
                "normal"
            }
        }
    )


    if not cases or not controls:
        raise ValueError(
            "CNV cohort comparison requires both Cancer and Healthy samples"
        )


    def key(row):

        if key_name == "region":
            return _event_key(row)

        return f"{row[key_name]}|{row['event_type']}"


    results=[]


    features = sorted(
        {
            key(r)
            for r in rows
            if r["event_type"] in {
                "GAIN",
                "LOSS"
            }
        }
    )


    for feature in features:

        present = [
            r
            for r in rows
            if key(r)==feature
        ]


        case_carriers = {
            r["sample_id"]
            for r in present
            if r["sample_id"] in cases
        }


        control_carriers = {
            r["sample_id"]
            for r in present
            if r["sample_id"] in controls
        }


        a=len(case_carriers)
        b=len(control_carriers)

        c=len(cases)-a
        d=len(controls)-b


        case_frequency=a/len(cases)
        control_frequency=b/len(controls)


        results.append(
            {
                "feature":feature,
                "event_type":present[0]["event_type"],

                "case_carriers":a,
                "control_carriers":b,

                "case_n":len(cases),
                "control_n":len(controls),

                "case_frequency":case_frequency,
                "control_frequency":control_frequency,

                "frequency_difference":
                    case_frequency-control_frequency,

                "effect_size":
                    abs(
                        case_frequency-control_frequency
                    ),

                "p_value":
                    fisher_exact_2x2(
                        a,b,c,d
                    )
            }
        )


    return add_fdr(results)



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


    significant=filter_significant(
        region_comparison,
        alpha=alpha
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