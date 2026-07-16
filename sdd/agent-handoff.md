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

- Implementation, tests, Dockerfile, CI, SDD, OpenSpec, README, and references are staged.
- Host feedback: 38 tests passed and the reduced 200/400-row scenarios behaved as expected.
- Host results are not publication evidence.
- The reuse kit has a staged monitoring-batch schema, model-monitoring skill for Codex/Claude, documentation, component-pack update, installer update, and kit validation.
- Docker build, transitive freeze, coverage in the exact image, three 2,000-row runs, aggregation, Desktop synchronization, GitHub publication, and public CI remain pending.

## Verification Order When Docker Returns

1. Build `model-drift-detector` and record image ID and size.
2. Freeze transitive dependencies from that image and rebuild.
3. Run Ruff and all tests with coverage threshold at least 90%.
4. Exercise tampered manifest, validation CLI, detect CLI, and Prometheus output.
5. Run one short CI benchmark and validate JSON.
6. Run three complete 2,000-row benchmarks on the same image.
7. Preserve raw outputs and failures, then aggregate median and range.
8. Update README opening and SDD evidence; set `evidence_status: current`.
9. Run the strict project validator.
10. Publish the reuse kit first, synchronize its exact commit, then publish #22.
11. Set repository description/topics and confirm GitHub Actions is green.

## Known Risks

- SciPy 1.18.0 and NumPy 2.5.1 integration is not verified in the pinned image yet.
- Direct dependencies are exact but transitive versions are not frozen.
- The new project declaration validator has only one strict consumer so far; #21 or #23 should exercise the producer side before it becomes a frozen v2 contract.
- KS does not detect correlation-only multivariate shift; this limitation is intentional and measured separately.
- A fixed 0.125 feature share is specific to the eight-feature fixture and must not be presented as a universal default.
