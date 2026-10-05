from pathlib import Path
import json
from wgr_cdp.research.a5_integration import write_a5_artifacts

def test_a5_writes_integrated_artifacts(tmp_path):
    candidates=[
        {"feature":"1:100:A:T","gene":"TP53","p_value":0.001,"q_value":0.01,
         "evidence_score":80,"functional_evidence":{"gene":"TP53","impact":"HIGH"}},
        {"feature":"1:200:G:C","gene":"GENE2","p_value":0.5,"q_value":0.8,
         "evidence_score":20},
    ]
    result=write_a5_artifacts(tmp_path,candidates,literature_search=False)
    assert result["ranked_count"] == 2
    for name in ("candidate_evidence.csv","candidate_constraints.json","literature_whitespace.json","ranking_sensitivity.json"):
        assert (Path(tmp_path)/name).exists()
    lit=json.loads((Path(tmp_path)/"literature_whitespace.json").read_text())
    assert lit["searched"] is False
    assert lit["records"] == []

def test_a5_hard_constraint_excludes_candidate(tmp_path):
    candidates=[
        {"feature":"A","q_value":0.001,"detectability":0.9,"constraints":{"assay_ok":True,"fpr_ok":True}},
        {"feature":"B","q_value":0.001,"detectability":0.1,"constraints":{"assay_ok":True,"fpr_ok":True}},
    ]
    result=write_a5_artifacts(tmp_path,candidates,
        constraints={"min_detectability":0.5},literature_search=False)
    assert result["ranked_count"] == 1
    assert result["ineligible_count"] == 1


def test_restrictive_background_ceiling_requires_observed_measurement(tmp_path):
    candidates = [
        {"feature": "A", "q_value": 0.01, "detectability": 0.9,
         "blood_background_safety": "Data unavailable"},
        {"feature": "B", "q_value": 0.01, "detectability": 0.9,
         "blood_background_safety": 0.96},
    ]
    result = write_a5_artifacts(
        tmp_path,
        candidates,
        constraints={"max_background": 0.1},
        literature_search=False,
    )
    assert result["ranked_count"] == 1
    assert result["ineligible_count"] == 1
    assert result["unscored_count"] == 0
