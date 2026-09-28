"""Transparent candidate evidence scoring."""


def score_candidate(result):
    """Calculate a bounded evidence score from documented signals.

    The score is a research prioritization aid, not a clinical probability,
    diagnostic result, or proof of biomarker status.
    """
    score = 0.0

    frequency_difference = abs(float(result.get("frequency_difference", 0.0)))
    # A 0.50+ absolute cohort-frequency separation receives the full
    # 40-point cohort-separation component.
    score += min(40.0, (frequency_difference / 0.5) * 40.0)

    p_value = result.get("p_value")
    if p_value is not None:
        p_value = float(p_value)
        if p_value <= 0.01:
            score += 30.0
        elif p_value <= 0.05:
            score += 10.0

    annotation = result.get("annotation") or {}
    functional = result.get("functional_evidence") or {}

    if annotation.get("clinvar_id") or annotation.get("clinvar_accession"):
        score += 10.0

    if annotation.get("dbsnp_rsids") or annotation.get("dbsnp_ref_snp_id"):
        score += 5.0

    if functional.get("gene"):
        score += 5.0

    if functional.get("consequence"):
        score += 5.0

    if functional.get("impact"):
        score += 5.0

    return min(100.0, score)
