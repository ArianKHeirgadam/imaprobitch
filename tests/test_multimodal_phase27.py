from wgr_cdp.multimodal.engine import analyze_multimodal_features, build_patient_candidate_matrix, detectability_curve, optimize_panel, scan_multiresolution


def test_multimodal_feature_types_and_regions():
    rows=[
      {"patient":"C1","group":"cancer","region":"17:100-100","feature_type":"SNV","value":"1","status":"Detected"},
      {"patient":"C2","group":"cancer","region":"17:100-100","feature_type":"SNV","value":"1","status":"Detected"},
      {"patient":"H1","group":"healthy","region":"17:100-100","feature_type":"SNV","value":"1","status":"Not detected"},
      {"patient":"C1","group":"cancer","region":"17:100-200","feature_type":"CNV","value":"2","status":"Detected"},
    ]
    out=analyze_multimodal_features(rows)
    assert set(out)=={"SNV","CNV"}
    assert out["SNV"][0]["case_frequency"]==1.0
    assert scan_multiresolution(rows)


def test_patient_candidate_panel():
    rows=[
      {"patient":"P1","region":"17:1-10","feature_type":"SNV","status":"Detected"},
      {"patient":"P2","region":"17:1-10","feature_type":"SNV","status":"Detected"},
      {"patient":"P2","region":"1:1-10","feature_type":"CNV","status":"Detected"},
      {"patient":"P3","region":"1:1-10","feature_type":"CNV","status":"Detected"},
    ]
    m=build_patient_candidate_matrix(rows); p=optimize_panel(m,2)
    assert p["covered_patients"]==3
    assert len(p["selected"])<=2


def test_detectability_supports_low_tumor_fraction():
    curve=detectability_curve([0.5,0.05,0.005],depth=300)
    assert len(curve)==3
    assert curve[0]["power"]>=curve[-1]["power"]
