from dataclasses import dataclass
from typing import Optional

STATUSES={"Detected","Not detected","Data unavailable"}

@dataclass(frozen=True)
class FeatureObservation:
    region:str
    patient:str
    feature_type:str
    value:Optional[float]
    status:str
    source:Optional[str]=None
    depth:Optional[float]=None
    vaf:Optional[float]=None
    copy_number:Optional[float]=None
    beta:Optional[float]=None
    m_value:Optional[float]=None
    heteroplasmy:Optional[float]=None
    def __post_init__(self):
        if self.status not in STATUSES: raise ValueError(f"invalid status: {self.status}")
        if not self.region or not self.patient or not self.feature_type: raise ValueError("region, patient and feature_type are required")
        if self.status=="Data unavailable" and self.value is not None: raise ValueError("Data unavailable cannot carry a value")
