# WGR-CDP Phase 3 Status

## Scope
Real feature-extraction interfaces are implemented for SNV/Indel/SV, CNV, methylation, PMD regions, repeat methylation and mitochondrial observations.

## Implementation
- Common FeatureObservation schema with explicit Detected / Not detected / Data unavailable states.
- VCF parser with PASS filtering, sample genotype handling, SNV/Indel/SV classification, VAF and depth extraction.
- CNV/SV tabular parsers.
- Methylation beta/M-value loader.
- PMD region loader and repeat-methylation loader.
- Mitochondrial heteroplasmy/copy-number loader.
- Dedicated Phase 3 tests.

## Data integrity
No external biological dataset was downloaded or analyzed by this implementation. No biological findings or diagnostic performance are claimed. Missing measurements remain Data unavailable and are never converted into negative evidence.

## Limitation
PMD calling from raw sequencing data requires a validated caller and suitable inputs; this phase provides a loss-aware loader for externally produced PMD regions rather than fabricating calls. CNV/SV and methylation loaders consume explicitly supplied tables.

## Gate
Implementation: PASS.
Scientific GO: pending CI execution of the complete test suite on the resulting commit.

Phase 4 cannot begin until CI passes and the Phase 3 GO decision is recorded.