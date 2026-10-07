# Phase A14 — SNV/INDEL Detection Engine

Status: IMPLEMENTED — real-data validation path added; awaiting local verification.

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
- real cancer-side validation of normalized TCGA-STAD VCFs
- explicit refusal to invent an independent healthy control group

Real-data validation boundary:
- The open TCGA-STAD subset is GDC masked somatic MAF-derived data.
- The normalized subset validates cancer-side SNV/INDEL extraction.
- TCGA matched normals are paired comparators, not an independent healthy population.
- No cancer-vs-healthy inference is reported until an independent healthy/control VCF cohort is supplied.
- 1000 Genomes may serve as a population/germline reference, but must not be relabeled as a gastric healthy cohort.

Not yet CLOSED:
- local pytest verification after the latest A14 changes
- real TCGA-STAD normalized VCF validation run
- scientific review of real-data outputs
- independent healthy/control cohort for cancer-vs-control inference
