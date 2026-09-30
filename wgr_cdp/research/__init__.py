"""Publication-oriented WGR-CDP scientific completion components."""
from .cfdna import detectability_probability, power_curve, estimate_lod, patient_candidate_matrix
from .multires_scanner import exact_scan, coarse_to_fine_scan
from .panel_optimizer import panel_coverage, greedy_panel, ilp_panel, alpha_budget
from .validation import AnalysisState, LeakageGuard, bootstrap_selection, cohort_holdout_guard
from .statistics import benjamini_hochberg, fisher_exact_2x2, per_feature_alpha, cohen_h
from .cfdna_score_engine import detectability_score
from .cfdna_simulator import simulate_detectability, validate_analytical_against_simulation

__all__ = [
    "detectability_probability","power_curve","estimate_lod","patient_candidate_matrix",
    "exact_scan","coarse_to_fine_scan","panel_coverage","greedy_panel","ilp_panel",
    "alpha_budget","AnalysisState","LeakageGuard","bootstrap_selection",
    "cohort_holdout_guard","benjamini_hochberg","fisher_exact_2x2",
    "per_feature_alpha","cohen_h","detectability_score","simulate_detectability","validate_analytical_against_simulation",
]