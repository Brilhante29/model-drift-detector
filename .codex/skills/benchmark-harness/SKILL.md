---
name: benchmark-harness
description: Add, run, or validate reproducible benchmarks for portfolio repositories. Use when the user asks for benchmark scripts, k6 tests, latency/throughput/recall/cost metrics, benchmark JSON, p95/p99 comparison, or README benchmark tables.
---

# Benchmark Harness

Use benchmarks as product evidence.

1. Prefer one primary metric and at most two secondary metrics.
2. Make the benchmark deterministic: fixed seed, fixed fixture, documented environment.
3. Write machine-readable JSON to `benchmarks/results/`.
4. Put the headline metric in the first screen of README.
5. Use `harness/bench.py` for generic command latency when no domain-specific runner exists.
6. Use k6 for HTTP services and define executable latency, check-rate, and failure-rate thresholds.
7. Keep warm-up or setup traffic outside custom measured metrics. Compute throughput as measured iterations divided by the configured measured duration, not from setup-inclusive k6 rates.
8. When a custom summary reads `p(99)`, include `p(99)` in `summaryTrendStats`; k6 does not include it in the default summary trend set.
9. Run a confirmation benchmark and report variance for the primary metric.
10. Compare old vs new results with `harness/compare_results.py` when optimizing an existing baseline.
11. Keep committed publication evidence stable during CI. A CI smoke run writes to a distinct path and artifact name, then receives its own schema, provenance, and failure-gate validation.
12. Validate README-to-result consistency against the committed canonical result before running a smoke benchmark. Never require static README text to predict a runner-specific latency value.
13. Keep V2 workload size and repetition count distinct: `workload.measured_iterations` is the number of domain work items in one repetition, while `execution.repeat` is the number of independent repetitions. When each metric stores one aggregate sample per repetition, its sample count must equal `execution.repeat`.
14. On Linux, a benchmark container that writes evidence to a bind mount must run with the host UID/GID or use an equivalently explicit ownership setup. Apply this to the short-lived writer only; do not weaken non-root users for long-running services.
15. Treat command-line workload overrides as evidence inputs. Rows, duration, repetitions, concurrency, and provider overrides must update `workload`, `comparability_key`, and the effective `config_digest`; assert the raw result reports the requested workload. A CI smoke artifact must never inherit canonical workload values it did not execute.
16. When CI installs an editable Python package before enforcing a clean Git tree, ignore generated `*.egg-info/` and coverage/cache outputs. Keep the clean-tree gate; do not waive it to accommodate generated metadata.

Do not report a benchmark without the command needed to reproduce it, its measured window, warm-up policy, result JSON, and failure gates.
