from wgr_cdp.research.a7_final_panel import build_final_panel, multimodal_to_candidates

W={"biological_evidence":1,"statistical_strength":1,"detectability":1,"blood_background_safety":1,
"early_stage_score":1,"specificity_score":1,"literature_novelty":1,"literature_validation_gap":1,"literature_diagnostic_utility":1}

def test_multimodal_candidates_preserve_unavailable():
    rows=[{"feature":"8:100-200|CNV","feature_type":"CNV","detectability":"","blood_background":"",
           "early_stage_fraction":"0.5","specificity":"0.8","validation_status":""}]
    out=multimodal_to_candidates(rows)
    assert out[0]["detectability"]=="Data unavailable"
    assert out[0]["blood_background_safety"]=="Data unavailable"
    assert out[0]["early_stage_score"]==0.5

def test_final_panel_uses_real_matrix_when_keys_match():
    c=[{"candidate_id":"A","feature":"A","detectability":.9,"blood_background_safety":.9,
        "early_stage_score":.8,"specificity_score":.8,"statistical_strength":.9,"biological_evidence":.8},
       {"candidate_id":"B","feature":"B","detectability":.8,"blood_background_safety":.9,
        "early_stage_score":.7,"specificity_score":.7,"statistical_strength":.8,"biological_evidence":.7}]
    m={"P1":{"A":.9,"B":.1},"P2":{"A":.1,"B":.9}}
    r=build_final_panel(c,m,2,weights=W)
    assert r["status"]=="Available"
    assert r["panel"]["status"]=="Available"
    assert r["panel"]["k"]==2
    assert 0<=r["panel"]["coverage"]<=1
    assert 0<r["panel"]["alpha_per_feature"]<.05

def test_final_panel_missing_matrix_is_explicit():
    c=[{"candidate_id":"A","feature":"A","statistical_strength":.9}]
    r=build_final_panel(c,None,1,weights=W)
    assert r["panel"]["status"]=="Data unavailable"
