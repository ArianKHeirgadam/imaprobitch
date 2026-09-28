"""Case/control variant and gene cohort comparison."""


from .models import normalize_cohort
from .statistics import fisher_exact_2x2


def _group_samples(samples):
    return {
        "case": [s for s in samples if s["group"] == "case"],
        "control": [s for s in samples if s["group"] == "control"],
    }


def _carrier_counts(samples, key):
    counts = {}

    for sample in samples:
        values = sample.get(key) or []
        for value in set(values):
            counts[value] = counts.get(value, 0) + 1

    return counts


def _compare_keys(case_samples, control_samples, case_counts, control_counts):
    case_n = len(case_samples)
    control_n = len(control_samples)

    keys = sorted(
        set(case_counts) | set(control_counts),
        key=str,
    )

    results = []

    for key in keys:
        case_carriers = case_counts.get(key, 0)
        control_carriers = control_counts.get(key, 0)

        case_rate = case_carriers / case_n if case_n else 0.0
        control_rate = control_carriers / control_n if control_n else 0.0

        if control_rate == 0.0:
            effect_ratio = float("inf") if case_rate > 0 else 1.0
        else:
            effect_ratio = case_rate / control_rate

        p_value = fisher_exact_2x2(
            case_carriers,
            control_carriers,
            case_n - case_carriers,
            control_n - control_carriers,
        )

        results.append({
            "feature": key,
            "case_carriers": case_carriers,
            "control_carriers": control_carriers,
            "case_n": case_n,
            "control_n": control_n,
            "case_frequency": case_rate,
            "control_frequency": control_rate,
            "frequency_difference": case_rate - control_rate,
            "case_control_frequency_ratio": effect_ratio,
            "p_value": p_value,
        })

    return results


def compare_variant_cohorts(samples):
    """Compare variant carrier frequencies between case and control groups."""
    normalized = normalize_cohort(samples)
    groups = _group_samples(normalized)

    if not groups["case"] or not groups["control"]:
        raise ValueError("both case and control samples are required")

    return _compare_keys(
        groups["case"],
        groups["control"],
        _carrier_counts(groups["case"], "variants"),
        _carrier_counts(groups["control"], "variants"),
    )


def _gene_variants(sample):
    genes = set()
    for variant in sample.get("variant_records") or []:
        gene = variant.get("gene")
        if gene:
            genes.add(gene)
    return genes


def compare_gene_cohorts(samples):
    """Compare carrier frequencies for genes represented in variant records."""
    normalized = normalize_cohort(samples)

    # Keep normalized sample metadata while deriving gene carrier sets.
    enriched = []
    for sample in normalized:
        enriched.append({
            **sample,
            "genes": _gene_variants(sample),
        })

    groups = _group_samples(enriched)

    if not groups["case"] or not groups["control"]:
        raise ValueError("both case and control samples are required")

    return _compare_keys(
        groups["case"],
        groups["control"],
        _carrier_counts(groups["case"], "genes"),
        _carrier_counts(groups["control"], "genes"),
    )
