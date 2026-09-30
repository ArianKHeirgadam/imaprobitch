"""Patient-aware cfDNA detectability, power and LoD models."""
from math import comb

DEFAULT_TUMOR_FRACTIONS=(0.5,0.2,0.1,0.05,0.02,0.01,0.005)

def _binom_tail(n,p,minimum):
    n=int(n); p=max(0,min(1,float(p))); minimum=int(minimum)
    if n<=0 or minimum>n or p==0: return 0.0
    if minimum<=0 or p==1: return 1.0
    return sum(comb(n,k)*p**k*(1-p)**(n-k) for k in range(minimum,n+1))

def alternate_fraction(tumor_fraction,copy_number=2.0,dilution=1.0,error_rate=0.001):
    tf=max(0,min(1,float(tumor_fraction))); cn=max(.1,float(copy_number))
    dilution=max(0,min(1,float(dilution))); error=max(0,min(1,float(error_rate)))
    return max(0,min(1,tf*dilution/cn+error))

def detectability_probability(tumor_fraction,depth=300,informative_sites=1,copy_number=2.0,dilution=1.0,error_rate=0.001,min_alt_reads=3,blood_background=0.0):
    depth=int(depth); sites=max(1,int(informative_sites)); bg=max(0,min(1,float(blood_background)))
    p=alternate_fraction(tumor_fraction,copy_number,dilution,error_rate)*(1-bg)
    single=_binom_tail(depth,p,min_alt_reads)
    return 1-(1-single)**sites

def power_curve(tumor_fractions=None,depths=(100,300,1000),**kwargs):
    fractions=tuple(tumor_fractions or DEFAULT_TUMOR_FRACTIONS)
    return [{"tumor_fraction":f,"depth":d,"power":detectability_probability(f,depth=d,**kwargs)} for d in depths for f in fractions]

def estimate_lod(depth=300,target_power=.95,lower=1e-5,upper=.5,**kwargs):
    if not 0<target_power<1: raise ValueError("target_power must be in (0,1)")
    if detectability_probability(upper,depth=depth,**kwargs)<target_power: return None
    lo,hi=float(lower),float(upper)
    for _ in range(60):
        mid=(lo+hi)/2
        if detectability_probability(mid,depth=depth,**kwargs)>=target_power: hi=mid
        else: lo=mid
    return hi

def patient_candidate_matrix(patients, candidates, candidate_features, assay=None):
    """Build D[p,c] using patient-specific candidate evidence when supplied."""
    out = {}
    for patient in patients:
        out[patient] = {}
        patient_features = candidate_features.get(patient) if isinstance(candidate_features.get(patient), dict) else {}
        for candidate in candidates:
            raw = patient_features.get(candidate) if isinstance(patient_features, dict) else None
            if raw is None:
                raw = candidate_features.get(candidate)
            s = dict(raw or {})
            if s.get("present") is False:
                out[patient][candidate] = 0.0
                continue
            out[patient][candidate] = detectability_probability(
                s.get("tumor_fraction", .01),
                depth=s.get("depth", 300),
                informative_sites=s.get("informative_sites", 1),
                copy_number=s.get("copy_number", 2),
                dilution=s.get("dilution", 1),
                error_rate=s.get("error_rate", .001),
                min_alt_reads=s.get("min_alt_reads", 3),
                blood_background=s.get("blood_background", 0),
            )
    return out
