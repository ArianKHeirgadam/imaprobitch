# C-10 — Literature Evidence and Whitespace

C-10 completes the literature-evidence contract required by the WGR-CDP
specification. It builds on the existing A5 evidence layer rather than creating
a second scoring system.

## Search strategy

For each supplied candidate identity, the system combines the available
candidate/feature, gene, and region terms into an explicit OR expression and
runs three declared intents:

- core_cfDNA
- diagnostic_context
- validation_context

Every intent includes:

- gastric cancer
- cfDNA / ctDNA / plasma / liquid-biopsy context

The same query strategy is executed independently against:

- PubMed
- Europe PMC

Source counts are never merged.

## Provenance contract

Every retrieval record stores:

- candidate identity
- intent
- source
- exact query
- search date
- result count
- retrieval status
- manual review status

The canonical machine-readable artifact is c10.literature.v1.

## Interpretation

A search-result count is retrieval metadata. It does not prove biological
importance, novelty, diagnostic utility, or a validation gap.

Therefore:

- novelty remains Data unavailable until manual review.
- validation_gap remains Data unavailable until manual review.
- diagnostic_utility remains Data unavailable until manual review.

The framework never claims that no studies exist globally. It reports only the
declared search strategy and its recorded retrieval results.

## Missing-data behavior

Failed searches, unavailable APIs, and unperformed searches remain explicit
unavailable/not-searched states. No unavailable search result is converted to
zero or to negative evidence.

## Artifacts

C-10 writes:

- c10_literature_evidence.json
- c10_literature_evidence.csv

A5's existing literature_whitespace.json remains as a compatibility artifact.

## Scientific boundary

C-10 is a literature-retrieval and provenance layer. It does not establish
clinical sensitivity/specificity, diagnostic validity, assay LoD, biological
causality, or global literature novelty.
