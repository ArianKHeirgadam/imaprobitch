"""Canonical Phase A6 ablation API."""
from .a6_validation import A6_ABLATIONS, run_ablations, compare_baseline
def compare(results):
    keys={"patient_coverage","lod","fpr","runtime","panel_stability","coverage"}
    return [{"ablation":name,**{k:v for k,v in dict(results[name]).items() if k in keys}} for name in A6_ABLATIONS if name in results]
