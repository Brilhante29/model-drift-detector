# Intent: model-drift-detector

## Measurable Claim

One local-first Docker command verifies immutable monitoring batches, detects univariate data and prediction drift with Holm-corrected KS evidence plus a minimum effect, and scores alarm F1 and false positives on deterministic labeled scenarios.

## Problem

Guards the model lifecycle from #21 after deployment by turning immutable feature and prediction batches into auditable drift alarms and labeled benchmark evidence.

## In Scope

- Use the selected component pack: `mlops-data-platform`.
- Keep the project under the MLOps and Data Platform program.
- Preserve the benchmark contract: `drift_alarm_f1` in `benchmarks/results/summary.json`.
- Keep the default path local-first and reproducible.

## Out Of Scope

- Paid credentials for the default demo.
- External infrastructure that is not required by the benchmark.
- Replacing local portfolio skills with external components silently.

## Default Demo Path

- Status: implemented
- Runtime: Single non-root Python 3.12.13 container pinned by OCI digest; CPU-only deterministic benchmark with no network or credentials at runtime.
- Benchmark command: `docker run --rm model-drift-detector`

## Public Proof

- Benchmark: drift_alarm_f1 = pending
- Result path: `benchmarks/results/summary.json`
