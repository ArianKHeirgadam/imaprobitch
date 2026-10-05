"""Leakage guards, frozen states and bootstrap selection stability."""
from enum import Enum
from random import Random

class AnalysisState(str,Enum):
    DISCOVERY="DISCOVERY"; FROZEN="FROZEN"; VALIDATION="VALIDATION"

class LeakageGuard:
    def __init__(self): self.state=AnalysisState.DISCOVERY
    def freeze(self): self.state=AnalysisState.FROZEN
    def enter_validation(self):
        if self.state!=AnalysisState.FROZEN: raise RuntimeError("validation requires a frozen analysis")
        self.state=AnalysisState.VALIDATION
    def require(self,state):
        if self.state!=state: raise RuntimeError(f"operation requires {state.value}, current state is {self.state.value}")

def bootstrap_selection(samples,selector,n_bootstrap=200,seed=42):
    rng=Random(seed); samples=list(samples); counts={}
    if not samples: return counts
    for _ in range(n_bootstrap):
        draw=[samples[rng.randrange(len(samples))] for _ in samples]
        for c in selector(draw): counts[c]=counts.get(c,0)+1
    return {c:n/n_bootstrap for c,n in counts.items()}

def cohort_holdout_guard(discovery_ids,validation_ids):
    overlap=set(discovery_ids)&set(validation_ids)
    if overlap: raise ValueError(f"cohort leakage detected: {sorted(overlap)}")
    return True

def patient_level_split(patient_ids, validation_fraction=0.2, test_fraction=0.2, seed=42):
    """Deterministically split unique patients; no patient can cross partitions."""
    ids=sorted({str(x) for x in patient_ids if x not in (None, "")})
    vf=float(validation_fraction); tf=float(test_fraction)
    if vf < 0 or tf < 0 or vf + tf >= 1:
        raise ValueError("validation_fraction + test_fraction must be in [0, 1)")
    rng=Random(seed)
    rng.shuffle(ids)
    n=len(ids)
    n_test=int(n*tf)
    n_validation=int(n*vf)
    test=ids[:n_test]
    validation=ids[n_test:n_test+n_validation]
    discovery=ids[n_test+n_validation:]
    return {
        "discovery": discovery,
        "validation": validation,
        "test": test,
        "seed": int(seed),
        "counts": {"discovery": len(discovery), "validation": len(validation), "test": len(test)},
    }


def audit_three_way_split(discovery_ids, validation_ids, test_ids):
    """Require mutually disjoint patient-level cohorts."""
    cohorts={
        "discovery": {str(x) for x in discovery_ids if x not in (None, "")},
        "validation": {str(x) for x in validation_ids if x not in (None, "")},
        "test": {str(x) for x in test_ids if x not in (None, "")},
    }
    overlaps={}
    names=list(cohorts)
    for i,left in enumerate(names):
        for right in names[i+1:]:
            overlap=sorted(cohorts[left] & cohorts[right])
            if overlap:
                overlaps[f"{left}__{right}"]=overlap
    return {
        "status": "FAIL" if overlaps else ("Available" if all(cohorts.values()) else "Data unavailable"),
        "leakage_free": bool(not overlaps and all(cohorts.values())),
        "counts": {name: len(values) for name, values in cohorts.items()},
        "overlaps": overlaps,
    }
