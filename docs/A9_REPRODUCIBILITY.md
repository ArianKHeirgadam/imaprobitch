# A9 — Final Reproducibility & Release Gate

A9 is the release-hardening layer after A8. It is additive and does not replace
scientific analysis.

## What it records

- release/version metadata;
- Python version and platform;
- pipeline configuration;
- run identifier;
- every output artifact path;
- file size;
- SHA-256 checksum;
- explicit scientific/clinical scope.

The manifest is generated from the actual run output directory, so it does not
invent biological results.

## Artifacts

Each completed run can contain:

- \`reproducibility_manifest.json\`

This manifest is a provenance record, not a biological validation result.

## Release gate

The A9 release gate checks software health and confirms that reproducibility
manifest support exists. Scientific results remain \`CONDITIONAL\` because
real-data empirical validation is separate from software release readiness.

## Freeze rule

A0–A8 scientific APIs remain unchanged by A9.
