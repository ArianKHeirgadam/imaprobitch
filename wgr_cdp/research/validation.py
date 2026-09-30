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