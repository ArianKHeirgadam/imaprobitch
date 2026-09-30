"""Canonical WGR-CDP ablation definitions."""
ABLATIONS=("full_wgr_cdp","without_detectability","without_complementary_optimization","without_blood_background","single_layer","multilayer","exact_scan_only","coarse_to_fine","without_early_stage","without_specificity")
def compare(results):
    keys={"patient_coverage","lod","fpr","runtime","panel_stability"}
    return [{"ablation":name,**{k:v for k,v in dict(results[name]).items() if k in keys}} for name in ABLATIONS if name in results]