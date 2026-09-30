"""Monte-Carlo validation for analytical cfDNA detectability models."""
from __future__ import annotations
from random import Random

def _binomial(rng, n, p):
    return sum(1 for _ in range(int(n)) if rng.random() < max(0.0, min(1.0, float(p))))

def simulate_detectability(
    tumor_fraction,
    depth=300,
    informative_sites=1,
    copy_number=2.0,
    dilution=1.0,
    error_rate=0.001,
    min_alt_reads=3,
    blood_background=0.0,
    simulations=10000,
    seed=42,
):
    """Estimate detection power empirically under the same assumptions as the analytical model."""
    if simulations <= 0:
        raise ValueError("simulations must be > 0")
    from .cfdna import alternate_fraction
    p = alternate_fraction(tumor_fraction, copy_number, dilution, error_rate)
    p *= 1.0 - max(0.0, min(1.0, float(blood_background)))
    rng = Random(seed)
    detected = 0
    for _ in range(int(simulations)):
        found = False
        for _ in range(max(1, int(informative_sites))):
            if _binomial(rng, depth, p) >= int(min_alt_reads):
                found = True
                break
        detected += int(found)
    return {
        "tumor_fraction": float(tumor_fraction),
        "depth": int(depth),
        "informative_sites": max(1, int(informative_sites)),
        "power": detected / int(simulations),
        "simulations": int(simulations),
        "seed": int(seed),
    }

def validate_analytical_against_simulation(analytical, simulated, tolerance=0.03):
    delta = abs(float(analytical) - float(simulated))
    return {"analytical": float(analytical), "simulated": float(simulated), "absolute_error": delta, "within_tolerance": delta <= tolerance}
