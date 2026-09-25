# WGR-CDP Phase 0 Repository Audit (Final)

Repository audited from uploaded archive:
GastricCancerDetection-main.zip

## Repository inventory

Files inspected: 86

Main stack:
- .NET 8 ASP.NET Core Web API
- Entity Framework Core
- SQL Server database-first mapping
- Python VCF parsing helper

Top-level structure:
- src/
  - GastricCancerDetection.API
  - GastricCancerDetection.Application
  - GastricCancerDetection.Domain
  - GastricCancerDetection.Infrastructure
- PythonScripts/
- SampleData/

## Current architecture

The repository implements a layered backend:

API
 -> Infrastructure
 -> Application
 -> Domain

The project is designed as an application platform rather than a research pipeline.

## Existing functionality

Verified:

1. Subject/sample management
2. Genome file upload workflow
3. VCF extraction through Python subprocess
4. Variant persistence
5. Gene-level comparison
6. Fisher exact test helper
7. Risk score/report generation

## Scientific assessment

Current workflow:

VCF
 -> fixed target genes
 -> gene-level aggregation
 -> statistical comparison
 -> risk score

This is not yet WGR-CDP.

## Reusable components

Keep:
- Domain entities for subjects, samples, genome files
- Database layer
- Analysis run persistence
- Python execution boundary
- Fisher exact test as baseline component

Do not use as WGR-CDP core:
- fixed gene panel discovery
- gene presence/absence scoring

## Missing WGR-CDP components

Missing:
- whole genome discovery
- multi-resolution scanner
- exact scanner
- CNV analysis
- methylation layer
- mitochondrial layer
- blood background model
- cfDNA detectability model
- patient x candidate matrix
- complementary panel optimization
- leakage guards
- reproducibility workflow
- validation framework

## Tests

No test project was found in the uploaded repository.

## Scientific risks

1. Fixed eight-gene search space creates discovery bias.
2. Gene-level aggregation loses regional and variant-level information.
3. No assay constraint modeling exists.
4. No independent validation exists.

## Phase 0 acceptance

Architecture documented: PASS
Existing functionality mapped: PASS
Scientific gaps documented: PASS
Full uploaded repository inspected: PASS
Novelty claim established: NO

## Decision

NO-GO for Phase 1.

Reason:
The repository audit is complete, but Phase 1 should not start until the project owner accepts the documented gaps and the transformation plan.
