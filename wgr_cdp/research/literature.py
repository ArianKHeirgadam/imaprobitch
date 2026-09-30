"""Reproducible literature-whitespace record model; no invented search counts."""
from datetime import datetime,timezone
def build_query(candidate,aliases=()):
    terms=[candidate,*aliases]
    return f"({' OR '.join(terms)}) AND (gastric cancer) AND (cfDNA OR ctDNA OR plasma OR liquid biopsy)"
def record(candidate,query,source,result_count=None,manual_review=False,searched_at=None):
    return {"candidate":candidate,"query":query,"source":source,"date":searched_at or datetime.now(timezone.utc).date().isoformat(),"result_count":result_count if result_count is not None else "Data unavailable","manual_review_status":"reviewed" if manual_review else "not_reviewed","novelty":"Data unavailable","validation_gap":"Data unavailable","diagnostic_utility":"Data unavailable"}