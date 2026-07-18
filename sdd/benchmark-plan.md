# Benchmark Plan: model-drift-detector

## Hypothesis

For the fixed supported scenario matrix, the explicit KS + Holm + effect policy detects mean, scale, and prediction shifts while preserving a low false-positive rate on stable batches.

## Primary Metric

- Name: `drift_alarm_f1`
- Unit: ratio
- Public result: `drift_alarm_f1 = 1.00`, median of three immutable Docker runs
- Command: `docker run --rm model-drift-detector`
- Result: `benchmarks/results/summary.json`

## Secondary Metrics

| Metric | Unit | Purpose |
|---|---:|---|
| precision | ratio | how often alarms are correct |
| recall | ratio | how many supported shifts alarm |
| false_positive_rate | ratio | stable-batch alert budget |
| detection_runtime_p50_ms | ms | typical comparison/policy time |
| detection_runtime_p95_ms | ms | tail comparison/policy time |
| blind_spot_detection_rate | ratio | visible behavior on excluded correlation-only drift |

## Inputs

- Reference seed: 42.
- Rows per batch: 2,000 for publication.
- Features: 8 numeric features plus one prediction score.
- Scored scenarios: 20 across stable, mean, scale, and prediction families.
- Unscored limitations: 2 correlation-only scenarios.
- Warm-up: 1 stable full evaluation.
- Runtime: CPU-only pinned Docker image.
- Repetitions: 3 complete runs on the same image and host conditions.

## Truth Independence

Scenario family, seed, shift magnitude, and scored status are constants in fixture generation. The detector receives only values and roles; it never receives truth, family, or seed. Thresholds were specified before the benchmark was executed. A local reduced run is development feedback and cannot become publication evidence.

## Measurement Boundary

Artifact generation, serialization, integrity verification, and loading are exercised before timing. Per-scenario `duration_ms` measures SciPy comparisons, Holm correction, effect checks, and alarm decision. Total container wall time is not mislabeled as detector latency.

## Aggregation

For each complete run, retain confusion counts, per-scenario decisions, per-column evidence, and runtime distribution. The publication summary uses median F1/FPR/p50/p95 and records min/max across the three runs. No failed or slow run may be discarded silently.

## Environment Evidence

Record date, OS/kernel, CPU/machine, Docker version, image ID and size, Python, NumPy, SciPy, rows, scenario count, container status, command, and failures.

## Acceptance Gates

- All 20 scored scenarios are present.
- Both correlation-only limitation scenarios are present and unscored.
- No malformed or missing per-column evidence.
- No benchmark failures.
- F1 and false-positive rate are computed from confusion counts.
- Prometheus output includes the evaluation metric.
- Result validates against the shared benchmark schema.
- README values are generated from current committed summary only.
