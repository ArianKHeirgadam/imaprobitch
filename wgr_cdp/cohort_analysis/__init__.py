"""Case/control cohort analysis for WGR-CDP."""

from .compare import compare_variant_cohorts, compare_gene_cohorts
from .models import normalize_cohort
from .statistics import fisher_exact_2x2

__all__ = [
    "compare_variant_cohorts",
    "compare_gene_cohorts",
    "normalize_cohort",
    "fisher_exact_2x2",
]
