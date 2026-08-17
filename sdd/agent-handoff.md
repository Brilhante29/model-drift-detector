# Agent Handoff: model-drift-detector

## Objective

Finish #22 as the post-deployment monitoring proof in the MLOps and Data Platform program, connected to #21 through a shared artifact rather than source-code imports.

## Accepted Decisions

- Program: `mlops-data-platform`.
- Architecture: evidence pipeline with narrow statistical and telemetry ports.
- API: local file-oriented CLI.
- Artifact: version 1 monitoring-batch manifest, CSV, size and SHA-256 before parse.
- Statistics: two-sided KS, Holm alpha 0.05, minimum KS effect 0.10.
- Alarm: feature share 0.125 or prediction drift.
- Benchmark: labeled supported scenarios plus an unscored correlation-only limitation.
- Cloud, Kumo, database, broker, orchestration, HTTP, and retraining: none.
- License: MIT.

## Current State

- The runtime, transitive lock, packaged/shared contracts, multi-stage Docker build, strict CI, and V2 producer are implemented.
- Python 3.12 container verification passes 48 tests at 91.22% coverage; Ruff passes.
- Monitoring comparisons now preserve and enforce producer, dataset, contract, model artifact, time-order, artifact, and feature-schema identity.
- Prior evidence was invalidated after the default non-root run exposed a post-`COPY` ownership defect.
- A corrected source commit, canonical evidence, GitHub publication, exact-SHA Actions verification, and reuse-kit promotion remain.

## Remaining Verification Order

1. Commit the readable summary and V2 publication artifact.
2. Run strict validation and push #22.
3. Verify GitHub Actions for the exact publication SHA.
4. Promote the monitoring skill and contract gates into the reuse kit.

## Known Risks

- The monitoring-batch schema has only one strict consumer; #21 should exercise the producer side before a breaking v2 contract.
- KS does not detect correlation-only multivariate shift; this limitation is intentional and measured separately.
- A fixed 0.125 feature share is specific to the eight-feature fixture and must not be presented as a universal default.
