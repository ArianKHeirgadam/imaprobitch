"""C-10 literature-whitespace and evidence provenance layer.

The module implements the specification's reproducible literature strategy:
candidate/gene/region terms + gastric cancer + cfDNA/ctDNA/plasma/liquid-biopsy
context, searched independently against PubMed and Europe PMC.

Search-result counts are not biological evidence. Novelty, validation-gap, and
diagnostic-utility assessments remain unavailable until an explicit manual
review is supplied.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

UNAVAILABLE = "Data unavailable"
REVIEW_STATUSES = ("Not reviewed", "In review", "Reviewed")
SOURCES = ("PubMed", "Europe PMC")
LIQUID_CONTEXT = '("cfDNA" OR "ctDNA" OR plasma OR "liquid biopsy")'


def _review_status(value):
    status = str(value or "Not reviewed")
    if status not in REVIEW_STATUSES:
        raise ValueError(
            f"manual_review_status must be one of {REVIEW_STATUSES!r}"
        )
    return status


def _unique_terms(candidate, aliases=()):
    values = [candidate, *aliases]
    out = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def build_queries(candidate, aliases=()):
    """Build the three declared literature intents for one candidate identity."""
    terms = _unique_terms(candidate, aliases)
    if not terms:
        raise ValueError("candidate or alias is required")
    term = "(" + " OR ".join(terms) + ")"
    disease = '"gastric cancer"'
    return [
        {
            "intent": "core_cfDNA",
            "query": f"{term} AND {disease} AND {LIQUID_CONTEXT}",
        },
        {
            "intent": "diagnostic_context",
            "query": f"{term} AND {disease} AND {LIQUID_CONTEXT} AND (diagnostic OR detection OR biomarker)",
        },
        {
            "intent": "validation_context",
            "query": f"{term} AND {disease} AND {LIQUID_CONTEXT} AND (validation OR cohort OR prospective)",
        },
    ]


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def search_pubmed(query, timeout=10, retmax=0):
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        "?db=pubmed&term=" + quote(query)
        + f"&retmode=json&retmax={int(retmax)}"
    )
    searched_at = _now_iso()
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {
            "source": "PubMed",
            "query": query,
            "date": searched_at,
            "result_count": int(payload["esearchresult"]["count"]),
            "status": "Available",
        }
    except Exception as exc:
        return {
            "source": "PubMed",
            "query": query,
            "date": searched_at,
            "result_count": UNAVAILABLE,
            "status": UNAVAILABLE,
            "error_type": type(exc).__name__,
        }


def search_europe_pmc(query, timeout=10, page_size=1):
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
        "format=json&query=" + quote(query)
        + f"&pageSize={int(page_size)}"
    )
    searched_at = _now_iso()
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {
            "source": "Europe PMC",
            "query": query,
            "date": searched_at,
            "result_count": int(payload.get("hitCount", 0)),
            "status": "Available",
        }
    except Exception as exc:
        return {
            "source": "Europe PMC",
            "query": query,
            "date": searched_at,
            "result_count": UNAVAILABLE,
            "status": UNAVAILABLE,
            "error_type": type(exc).__name__,
        }


def search_literature(query, sources=SOURCES, timeout=10):
    """Search declared sources independently; counts are never merged."""
    records = []
    for source in sources:
        if source == "PubMed":
            records.append(search_pubmed(query, timeout=timeout))
        elif source == "Europe PMC":
            records.append(search_europe_pmc(query, timeout=timeout))
        else:
            records.append({
                "source": str(source),
                "query": query,
                "date": _now_iso(),
                "result_count": UNAVAILABLE,
                "status": UNAVAILABLE,
                "error_type": "UnsupportedSource",
            })
    return records


def literature_record(
    candidate,
    aliases=(),
    search=False,
    sources=SOURCES,
    timeout=10,
    manual_review_status="Not reviewed",
):
    """Return provenance-bearing records for the three search intents."""
    review_status = _review_status(manual_review_status)
    records = []
    for item in build_queries(candidate, aliases):
        if search:
            source_records = search_literature(
                item["query"], sources=sources, timeout=timeout
            )
        else:
            source_records = [
                {
                    "source": str(source),
                    "query": item["query"],
                    "date": datetime.now(timezone.utc).date().isoformat(),
                    "result_count": UNAVAILABLE,
                    "status": "Not searched",
                }
                for source in sources
            ]
        for result in source_records:
            result.update({
                "candidate": str(candidate),
                "intent": item["intent"],
                "manual_review_status": review_status,
                "novelty": UNAVAILABLE,
                "validation_gap": UNAVAILABLE,
                "diagnostic_utility": UNAVAILABLE,
            })
            records.append(result)
    return records


def candidate_terms(row):
    """Resolve feature/gene/region identity without inventing biological aliases."""
    row = dict(row or {})
    values = [
        row.get("feature"),
        row.get("candidate_id"),
        row.get("candidate"),
        row.get("gene"),
        row.get("region"),
    ]
    return _unique_terms(values)


def build_candidate_literature_records(
    candidates,
    search=False,
    sources=SOURCES,
    timeout=10,
    manual_review_status="Not reviewed",
):
    """Search each supplied candidate identity as one explicit OR query group."""
    records = []
    for row in candidates:
        row = dict(row or {})
        terms = candidate_terms(row)
        if not terms:
            continue
        primary, aliases = terms[0], terms[1:]
        candidate_id = str(
            row.get("candidate_id")
            or row.get("feature")
            or row.get("candidate")
            or primary
        )
        for record in literature_record(
            primary,
            aliases=aliases,
            search=search,
            sources=sources,
            timeout=timeout,
            manual_review_status=manual_review_status,
        ):
            record["candidate_id"] = candidate_id
            record["search_terms"] = terms
            records.append(record)
    return records


def summarize_whitespace(records):
    """Summarize counts while preserving source and intent provenance."""
    grouped = {}
    for row in records:
        key = str(row.get("candidate_id") or row.get("candidate") or "")
        if not key:
            continue
        grouped.setdefault(key, []).append(row)

    output = {}
    for candidate_id, rows in grouped.items():
        counts_by_source = {}
        counts_by_intent = {}
        searchable_rows = 0
        available_rows = 0
        review_states = set()

        for row in rows:
            source = str(row.get("source", ""))
            intent = str(row.get("intent", ""))
            result_count = row.get("result_count")
            review_states.add(str(row.get("manual_review_status", "Not reviewed")))
            searchable_rows += int(row.get("status") in {"Available", UNAVAILABLE})

            if row.get("status") == "Available":
                available_rows += 1

            if isinstance(result_count, int):
                counts_by_source.setdefault(source, []).append(result_count)
                counts_by_intent.setdefault(intent, []).append(result_count)

        output[candidate_id] = {
            "query_count": len(rows),
            "searched_queries": searchable_rows,
            "available_queries": available_rows,
            "sources": sorted({str(row.get("source", "")) for row in rows if row.get("source")}),
            "intents": sorted({str(row.get("intent", "")) for row in rows if row.get("intent")}),
            "result_counts_by_source": counts_by_source,
            "result_counts_by_intent": counts_by_intent,
            "manual_review_status": (
                "Reviewed"
                if review_states == {"Reviewed"}
                else "In review"
                if "In review" in review_states
                else "Not reviewed"
            ),
            "novelty": UNAVAILABLE,
            "validation_gap": UNAVAILABLE,
            "diagnostic_utility": UNAVAILABLE,
            "status": "Available" if available_rows else UNAVAILABLE,
        }
    return output


def write_literature_evidence(
    output_dir,
    candidates,
    search=False,
    sources=SOURCES,
    timeout=10,
    manual_review_status="Not reviewed",
    records=None,
):
    """Write canonical C-10 JSON/CSV provenance artifacts."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    sources = tuple(str(source) for source in sources)
    for source in sources:
        if source not in SOURCES:
            raise ValueError(f"Unsupported literature source: {source!r}")

    records = list(records) if records is not None else build_candidate_literature_records(
        candidates,
        search=search,
        sources=sources,
        timeout=timeout,
        manual_review_status=manual_review_status,
    )
    summary = summarize_whitespace(records)
    payload = {
        "schema_version": "c10.literature.v1",
        "searched": bool(search),
        "sources": list(sources),
        "manual_review_status": _review_status(manual_review_status),
        "records": records,
        "summary": summary,
        "scientific_boundary": (
            "Search counts are provenance-bearing retrieval metadata only. "
            "Novelty, validation gap and diagnostic utility remain Data unavailable "
            "until an explicit manual literature review is supplied."
        ),
    }

    json_path = output / "c10_literature_evidence.json"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    csv_path = output / "c10_literature_evidence.csv"
    fields = [
        "candidate_id", "candidate", "intent", "source", "query", "date",
        "result_count", "status", "manual_review_status", "novelty",
        "validation_gap", "diagnostic_utility",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    return {
        "status": "Available" if candidates else UNAVAILABLE,
        "schema_version": "c10.literature.v1",
        "json": str(json_path),
        "csv": str(csv_path),
        "candidate_count": len({row.get("candidate_id") for row in records}),
        "record_count": len(records),
        "searched": bool(search),
        "sources": list(sources),
    }
