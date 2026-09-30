"""cfDNA detectability score and assay-feasibility layer."""
from __future__ import annotations
from .cfdna import detectability_probability, estimate_lod

REQUIRED_TUMOR_FRACTIONS=(0.5,0.2,0.1,0.05,0.02,0.01,0.005)

def detectability_score(
    tumor_fraction,
    depth=300,
    region_size=1,
    informative_sites=1,
    copy_number=2.0,
    error_rate=0.001,
    blood_background=0.0,
    min_alt_reads=3,
    feature_type="SNV",
):
    """Return probability plus explicit assay-feasibility metadata."""
    probability = detectability_probability(
        tumor_fraction,
        depth=depth,
        informative_sites=informative_sites,
        copy_number=copy_number,
        error_rate=error_rate,
        blood_background=blood_background,
        min_alt_reads=min_alt_reads,
    )
    feature_type = str(feature_type).upper()
    low_pass_limit = feature_type in {"SNV", "INDEL"} and int(depth) < 100
    return {
        "tumor_fraction": float(tumor_fraction),
        "depth": int(depth),
        "region_size": max(1, int(region_size)),
        "informative_sites": max(1, int(informative_sites)),
        "copy_number": float(copy_number),
        "error_rate": float(error_rate),
        "blood_background": float(blood_background),
        "feature_type": feature_type,
        "detectability_score": probability,
        "assay_feasibility": "limited_low_pass_SNV_INDEL" if low_pass_limit else "modeled",
    }

def detectability_profile(depths=(100,300,1000), tumor_fractions=REQUIRED_TUMOR_FRACTIONS, **kwargs):
    return [detectability_score(f, depth=d, **kwargs) for d in depths for f in tumor_fractions]

def lod_profile(depths=(100,300,1000), target_power=0.95, **kwargs):
    return [{"depth": d, "lod": estimate_lod(depth=d, target_power=target_power, **kwargs)} for d in depths]
