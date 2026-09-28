# Phase 17 — External Annotation Integration

Adds a stable integration boundary between normalized variant ingestion and annotation adapters.

## Added
- Annotation mapping to a stable internal schema.
- Adapter-based annotation pipeline.
- Explicit handling of missing annotations.
- Integration tests for adapter and no-annotation paths.

## Scope
This phase defines the integration interface; it does not bundle or hard-code external databases such as ClinVar or dbSNP.
