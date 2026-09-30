# Phase A5 — Candidate Evidence, Literature Whitespace, and Sensitivity

A5 adds an auditable evidence layer above discovery and cfDNA feasibility.

## Components
- evidence.py: normalized evidence fields, hard constraints before ranking, transparent weighted scoring.
- literature_whitespace.py: reproducible PubMed query generation and optional live ESearch records.
- early_stage.py: Stage I-II versus III-IV stratification.
- specificity.py: healthy and supplied differential comparator groups.
- sensitivity_analysis.py: weight normalization and ranking stability across scenarios.
- integrated_candidate.py: integration helpers.

## Evidence dimensions
Biological evidence, statistical strength, cfDNA detectability, blood-background safety, early-stage evidence, specificity, literature novelty, validation gap, and diagnostic utility are stored separately.

Missing evidence remains "Data unavailable" and is never silently converted to zero.

## Hard constraints
Assay/FPR constraints, detectability thresholds, and background constraints are evaluated before ranking. A candidate that fails a hard constraint is excluded from the ranked eligible set.

## Literature
PubMed ESearch is used only when explicitly requested by the caller with search=True. Each record stores the exact query, source, date, result count, and status. Failed or unperformed searches remain explicit unavailable/not-searched states.

NCBI documents ESearch as the Entrez interface for text queries and result sets. See:
https://www.ncbi.nlm.nih.gov/books/NBK25499/

## Scientific limitation
A5 does not claim novelty, clinical utility, or absence of literature globally. Those conclusions require actual searches and manual review of retrieved literature.

## End-to-end integration

The CLI now executes A5 after the existing real cohort/CNV analysis. Every run writes:

- `candidate_evidence.csv`
- `candidate_constraints.json`
- `literature_whitespace.json`
- `ranking_sensitivity.json`

The evidence layer consumes the actual discovery candidates and CNV candidates produced by the run; it does not create a separate synthetic candidate universe.

The CLI option `--literature-search` explicitly enables live PubMed ESearch. Without that flag, literature counts remain `Data unavailable` and the run records that no search was performed.

A5 remains research prioritization only. It does not convert evidence scores into diagnostic probabilities or clinical claims.
