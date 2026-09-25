"""Phase 2 QC and harmonization primitives."""
import re
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Exclusion:
    sample_id: str
    reason: str
    module: str
    timestamp: str


def normalize_chromosome(chrom):
    chrom = str(chrom)
    return chrom[3:] if chrom.startswith('chr') else chrom


def normalize_sample_id(sample_id):
    return re.sub(r'[^A-Za-z0-9_.-]', '_', str(sample_id))


def make_exclusion(sample_id, reason, module):
    return Exclusion(sample_id, reason, module, datetime.utcnow().isoformat())
