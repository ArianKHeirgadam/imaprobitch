"""Evaluation report builder."""


def build_report(candidate_id, metrics):
    return {
        "candidate_id": candidate_id,
        "metrics": metrics,
    }
