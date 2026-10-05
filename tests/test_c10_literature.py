from pathlib import Path
import json
import pytest

from wgr_cdp.research.literature_whitespace import (
    build_queries,
    build_candidate_literature_records,
    literature_record,
    search_literature,
    summarize_whitespace,
    write_literature_evidence,
)


def test_c10_queries_include_all_required_context():
    queries = build_queries("TP53", aliases=("P53", "17:7674220:C:T"))
    assert len(queries) == 3
    assert all("gastric cancer" in item["query"] for item in queries)
    assert all(("cfDNA" in item["query"] or "ctDNA" in item["query"]) for item in queries)
    assert all("intent" in item for item in queries)


def test_no_search_preserves_both_sources_and_unavailable_counts():
    records = literature_record("TP53", search=False)
    assert len(records) == 6
    assert {row["source"] for row in records} == {"PubMed", "Europe PMC"}
    assert all(row["result_count"] == "Data unavailable" for row in records)
    assert all(row["manual_review_status"] == "Not reviewed" for row in records)
    assert {row["intent"] for row in records} == {
        "core_cfDNA", "diagnostic_context", "validation_context"
    }


def test_search_literature_preserves_source_separation(monkeypatch):
    monkeypatch.setattr(
        "wgr_cdp.research.literature_whitespace.search_pubmed",
        lambda query, timeout=10: {
            "source": "PubMed", "query": query, "date": "x",
            "result_count": 3, "status": "Available",
        },
    )
    monkeypatch.setattr(
        "wgr_cdp.research.literature_whitespace.search_europe_pmc",
        lambda query, timeout=10: {
            "source": "Europe PMC", "query": query, "date": "x",
            "result_count": 5, "status": "Available",
        },
    )
    out = search_literature("TP53 AND gastric cancer")
    assert [row["result_count"] for row in out] == [3, 5]
    assert {row["source"] for row in out} == {"PubMed", "Europe PMC"}


def test_candidate_identity_uses_feature_gene_region_without_invention():
    records = build_candidate_literature_records(
        [{
            "candidate_id": "C1",
            "feature": "17:7674220:C:T",
            "gene": "TP53",
            "region": "17:7M",
        }],
        search=False,
    )
    assert len(records) == 6
    assert all(row["candidate_id"] == "C1" for row in records)
    assert all("TP53" in row["query"] for row in records)
    assert all("17:7M" in row["query"] for row in records)


def test_review_status_is_strict():
    with pytest.raises(ValueError):
        literature_record("TP53", manual_review_status="invented")


def test_summary_preserves_source_and_intent_counts():
    records = [
        {"candidate_id": "A", "source": "PubMed", "intent": "core_cfDNA",
         "status": "Available", "result_count": 10, "manual_review_status": "Not reviewed"},
        {"candidate_id": "A", "source": "Europe PMC", "intent": "core_cfDNA",
         "status": "Available", "result_count": 7, "manual_review_status": "Not reviewed"},
        {"candidate_id": "A", "source": "PubMed", "intent": "validation_context",
         "status": "Available", "result_count": 4, "manual_review_status": "Not reviewed"},
    ]
    summary = summarize_whitespace(records)
    assert summary["A"]["result_counts_by_source"] == {
        "Europe PMC": [7],
        "PubMed": [10, 4],
    }
    assert summary["A"]["result_counts_by_intent"]["core_cfDNA"] == [10, 7]
    assert summary["A"]["status"] == "Available"
    assert summary["A"]["novelty"] == "Data unavailable"


def test_c10_artifacts_are_written(tmp_path: Path):
    result = write_literature_evidence(
        tmp_path,
        [{"candidate_id": "C1", "feature": "17:7674220:C:T", "gene": "TP53"}],
        search=False,
    )
    assert result["schema_version"] == "c10.literature.v1"
    assert Path(result["json"]).exists()
    assert Path(result["csv"]).exists()
    payload = json.loads(Path(result["json"]).read_text(encoding="utf-8"))
    assert payload["sources"] == ["PubMed", "Europe PMC"]
    assert payload["records"]
    assert all(
        row["novelty"] == "Data unavailable"
        and row["validation_gap"] == "Data unavailable"
        and row["diagnostic_utility"] == "Data unavailable"
        for row in payload["records"]
    )
