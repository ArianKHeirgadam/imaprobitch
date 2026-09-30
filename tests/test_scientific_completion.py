from wgr_cdp.research.cfdna import detectability_probability,estimate_lod,patient_candidate_matrix
from wgr_cdp.research.multires_scanner import exact_scan,coarse_to_fine_scan
from wgr_cdp.research.panel_optimizer import panel_coverage,greedy_panel,ilp_panel,alpha_budget
from wgr_cdp.research.statistics import benjamini_hochberg,cohen_h
from wgr_cdp.research.validation import LeakageGuard,AnalysisState,cohort_holdout_guard

def rows():
    return [
      {"patient":"C1","group":"case","region":"1:100-100","feature_type":"SNV","status":"Detected","value":1},
      {"patient":"C2","group":"case","region":"1:100-100","feature_type":"SNV","status":"Detected","value":1},
      {"patient":"H1","group":"control","region":"1:100-100","feature_type":"SNV","status":"Not detected","value":0},
      {"patient":"H2","group":"control","region":"1:100-100","feature_type":"SNV","status":"Not detected","value":0}]

def test_cfdna_monotonic_and_lod():
    assert detectability_probability(.10,depth=300)>detectability_probability(.01,depth=300)
    assert estimate_lod(depth=300) is not None

def test_patient_matrix():
    m=patient_candidate_matrix(["P1"],["c1"],{"c1":{"tumor_fraction":.05,"depth":300}})
    assert 0<=m["P1"]["c1"]<=1

def test_scanner():
    assert len(exact_scan(rows()))==1
    assert len(coarse_to_fine_scan(rows())["final"])==1

def test_panel():
    m={"P1":{"a":.9,"b":.1},"P2":{"a":.1,"b":.9}}
    assert panel_coverage(m,["a","b"])>panel_coverage(m,["a"])
    assert len(greedy_panel(m,max_k=2)["selected"])==2
    assert ilp_panel(m,max_k=2)["status"]=="optimal"

def test_statistics():
    assert benjamini_hochberg([.01,.02])==[.02,.02]
    assert cohen_h(.9,.1)>0
    assert 0<alpha_budget(.05,5)<.05

def test_leakage():
    g=LeakageGuard(); g.freeze(); g.enter_validation(); assert g.state==AnalysisState.VALIDATION
    try: cohort_holdout_guard(["A"],["A"]); assert False
    except ValueError: pass