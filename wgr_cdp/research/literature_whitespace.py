"""Reproducible literature-whitespace search records."""
from __future__ import annotations
from datetime import datetime,timezone
from urllib.parse import quote
from urllib.request import urlopen
import json
def build_queries(candidate,aliases=()):
    terms=[str(candidate)]+[str(x) for x in aliases if str(x)]; term="("+" OR ".join(dict.fromkeys(terms))+")"; disease='"gastric cancer"'; liquid='("cfDNA" OR "ctDNA" OR plasma OR "liquid biopsy")'
    return [{"source":"PubMed","query":f"{term} AND {disease} AND {liquid}"},{"source":"PubMed","query":f"{term} AND {disease} AND (diagnostic OR detection OR biomarker)"},{"source":"PubMed","query":f"{term} AND {disease} AND (validation OR cohort OR prospective)"}]
def search_pubmed(query,timeout=10,retmax=0):
    url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term="+quote(query)+f"&retmode=json&retmax={int(retmax)}"; searched_at=datetime.now(timezone.utc).isoformat()
    try:
        with urlopen(url,timeout=timeout) as response: payload=json.loads(response.read().decode("utf-8"))
        return {"source":"PubMed","query":query,"date":searched_at,"result_count":int(payload["esearchresult"]["count"]),"status":"Available"}
    except Exception as exc:
        return {"source":"PubMed","query":query,"date":searched_at,"result_count":"Data unavailable","status":"Data unavailable","error_type":type(exc).__name__}
def literature_record(candidate,aliases=(),search=False):
    records=[]
    for item in build_queries(candidate,aliases):
        result=search_pubmed(item["query"]) if search else {"source":item["source"],"query":item["query"],"date":datetime.now(timezone.utc).date().isoformat(),"result_count":"Data unavailable","status":"Not searched"}
        result.update({"candidate":str(candidate),"novelty":"Data unavailable","validation_gap":"Data unavailable","diagnostic_utility":"Data unavailable"}); records.append(result)
    return records
def summarize_whitespace(records):
    grouped={}
    for row in records: grouped.setdefault(str(row.get("candidate","")),[]).append(row)
    out={}
    for candidate,rows in grouped.items():
        counts=[r["result_count"] for r in rows if isinstance(r.get("result_count"),int)]
        out[candidate]={"queries":len(rows),"searched_queries":sum(r.get("status")=="Available" for r in rows),"result_counts":counts,"status":"Available" if counts else "Data unavailable","novelty":"Data unavailable","validation_gap":"Data unavailable","diagnostic_utility":"Data unavailable"}
    return out
