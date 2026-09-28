"""Generate candidate profiles from cohort results and evidence."""


from .scoring import score_candidate


def _variant_key(row):
    return row.get("feature")


def discover_candidates(cohort_results, annotations=None, functional_evidence=None):
    """Combine cohort statistics with annotation evidence.

    Parameters are keyed by the cohort result's ``feature`` value. Missing
    evidence is represented by empty dictionaries.
    """
    annotations = annotations or {}
    functional_evidence = functional_evidence or {}

    candidates = []

    for row in cohort_results or []:
        key = _variant_key(row)
        annotation = dict(annotations.get(key) or {})
        functional = dict(functional_evidence.get(key) or {})

        candidate = dict(row)
        candidate["annotation"] = annotation
        candidate["functional_evidence"] = functional
        candidate["evidence_flags"] = {
            "clinvar": bool(
                annotation.get("clinvar_id")
                or annotation.get("clinvar_accession")
            ),
            "dbsnp": bool(
                annotation.get("dbsnp_rsids")
                or annotation.get("dbsnp_ref_snp_id")
            ),
            "functional": bool(
                functional.get("gene")
                or functional.get("consequence")
            ),
        }
        candidate["evidence_score"] = score_candidate(candidate)
        candidates.append(candidate)

    candidates.sort(
        key=lambda item: (
            -float(item.get("evidence_score", 0.0)),
            float(item.get("p_value", 1.0)),
            str(item.get("feature")),
        )
    )

    for index, candidate in enumerate(candidates, start=1):
        candidate["candidate_rank"] = index

    return candidates
