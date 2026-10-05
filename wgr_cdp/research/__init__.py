"""Publication-oriented WGR-CDP scientific completion components."""
from .cfdna import detectability_probability, power_curve, lod_curve, detectability_grid, estimate_lod, patient_candidate_matrix
from .multires_scanner import exact_scan, coarse_to_fine_scan
from .panel_optimizer import panel_coverage, greedy_panel, ilp_panel, alpha_budget
from .validation import AnalysisState, LeakageGuard, bootstrap_selection, cohort_holdout_guard
from .statistics import benjamini_hochberg, fisher_exact_2x2, per_feature_alpha, cohen_h
from .cfdna_score_engine import detectability_score
from .cfdna_simulator import simulate_detectability, validate_analytical_against_simulation
from .evidence import normalize_evidence, apply_constraints, transparent_weighted_score, rank_candidates
from .literature_whitespace import build_queries, search_pubmed, literature_record, summarize_whitespace
from .early_stage import stage_candidate_rates, early_stage_score
from .specificity import specificity_rates, specificity_score
from .sensitivity_analysis import normalize_weights, weight_sensitivity, selection_stability
from .blood_background import estimate_background, build_pon, annotate_pon, filter_candidates

__all__ = [
    "detectability_probability","power_curve","lod_curve","detectability_grid","estimate_lod","patient_candidate_matrix",
    "exact_scan","coarse_to_fine_scan","panel_coverage","greedy_panel","ilp_panel",
    "alpha_budget","AnalysisState","LeakageGuard","bootstrap_selection",
    "cohort_holdout_guard","benjamini_hochberg","fisher_exact_2x2",
    "per_feature_alpha","cohen_h","detectability_score","simulate_detectability","validate_analytical_against_simulation",
    "normalize_evidence","apply_constraints","transparent_weighted_score","rank_candidates",
    "build_queries","search_pubmed","literature_record","summarize_whitespace",
    "stage_candidate_rates","early_stage_score","specificity_rates","specificity_score",
    "normalize_weights","weight_sensitivity","selection_stability","estimate_background","build_pon","annotate_pon","filter_candidates",
]
from .a5_integration import write_a5_artifacts, DEFAULT_WEIGHTS
from .a6_validation import run_a6, conventional_feature_ranking, bootstrap_rank_stability
from .a8_validation import run_a8, audit_cohort_leakage, revalidate_selected
