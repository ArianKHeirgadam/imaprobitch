# Phase A14 — SNV/INDEL Detection Engine

Status: IMPLEMENTED — awaiting local verification.

Implemented:
- VCF/VCF.GZ SNV/INDEL extraction
- PASS filtering
- multi-allelic decomposition
- GT/DP/AD/AF parsing
- optional depth/VAF thresholds
- patient-level case/control statistics
- BH-FDR
- explicit unavailable semantics
- auditable CSV artifacts
- regression tests

Not yet CLOSED:
- local pytest verification
- real TCGA-STAD normalized VCF run
- scientific review of real-data outputs
