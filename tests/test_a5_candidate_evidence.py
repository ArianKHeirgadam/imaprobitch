from wgr_cdp.research.evidence import normalize_evidence,apply_constraints,transparent_weighted_score,rank_candidates
from wgr_cdp.research.literature_whitespace import build_queries,literature_record,summarize_whitespace
from wgr_cdp.research.early_stage import stage_candidate_rates
from wgr_cdp.research.specificity import specificity_rates,specificity_score
from wgr_cdp.research.sensitivity_analysis import normalize_weights,weight_sensitivity,selection_stability

def candidate(cid,**kw):
    row={"candidate_id":cid,"biological_evidence":.8,"statistical_strength":.9,"detectability":.8,"blood_background_safety":.95,"early_stage_score":.7,"specificity_score":.8,"literature":{"novelty":.6,"validation_gap":.7,"diagnostic_utility":.5},"constraints":{"assay_ok":True,"fpr_ok":True}}
    row.update(kw); return row

def test_evidence_normalization_and_constraints():
    row=normalize_evidence(candidate("A")); assert row["literature_novelty"]==.6
    assert apply_constraints(row,min_detectability=.5)["constraints"]["eligible"]

def test_constraints_precede_ranking():
    result=rank_candidates([candidate("A",detectability=.9),candidate("B",detectability=.1)],{"detectability":1},{"min_detectability":.5})
    assert [r["candidate_id"] for r in result["ranked"]]==["A"]; assert result["ineligible"][0]["candidate_id"]=="B"

def test_weighted_score_is_transparent():
    result=transparent_weighted_score(candidate("A"),{"detectability":.75,"specificity_score":.25})
    assert 0<=result["score"]<=1; assert set(result["used_fields"])=={"detectability","specificity_score"}

def test_unavailable_evidence_is_not_zero():
    result=transparent_weighted_score({"candidate_id":"X","detectability":"Data unavailable"},{"detectability":1})
    assert result["score"] is None and result["status"]=="Data unavailable"

def test_literature_query_generation():
    queries=build_queries("TP53",aliases=("P53",)); assert len(queries)==3
    assert all("gastric cancer" in q["query"] for q in queries)

def test_literature_no_search_does_not_invent_counts():
    records=literature_record("TP53",search=False)
    assert records and all(r["result_count"]=="Data unavailable" for r in records)

def test_literature_summary():
    summary=summarize_whitespace([{"candidate":"A","status":"Available","result_count":10},{"candidate":"A","status":"Available","result_count":4},{"candidate":"B","status":"Not searched","result_count":"Data unavailable"}])
    assert summary["A"]["result_counts"]==[10,4] and summary["B"]["status"]=="Data unavailable"

def test_stage_stratification():
    out=stage_candidate_rates([{"candidate":"A","stage":"I","detected":True},{"candidate":"A","stage":"II","detected":False},{"candidate":"A","stage":"III","detected":True},{"candidate":"A","stage":"IV","detected":True}])
    assert out["A"]["early_rate"]==.5 and out["A"]["late_rate"]==1.0

def test_specificity_comparators():
    out=specificity_rates([{"candidate":"A","group":"healthy","detected":False},{"candidate":"A","group":"healthy","detected":False},{"candidate":"A","group":"gastritis","detected":False},{"candidate":"A","group":"other_cancer","detected":True}])
    score=specificity_score(out["A"],target_groups=("healthy",),competing_groups=("gastritis","other_cancer")); assert 0<=score<=1

def test_sensitivity():
    rows=[candidate("A"),candidate("B",detectability=.6,specificity_score=.95)]
    assert sum(normalize_weights({"detectability":.5,"specificity_score":.5}).values())==1
    results=weight_sensitivity(rows,{"detectability":.5,"specificity_score":.5},[("detectability-heavy",{"detectability":2,"specificity_score":1}),("specificity-heavy",{"detectability":1,"specificity_score":2})])
    assert len(results)==2 and selection_stability(results)["n_scenarios"]==2
