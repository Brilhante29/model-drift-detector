# Component Pack: model-drift-detector

## Selected Pack

- Pack id: `mlops-data-platform`
- Pack name: MLOps and Data Platform
- Problem: Move models and data through training, validation, feature serving, drift detection, and streaming.

## Benchmark Focus

- time_to_production
- drift_alarm_delta
- feature_read_latency_ms
- rejected_rows_ratio
- messages_per_second

## Preferred Artifacts

- data contract
- feature schema
- model registry record
- drift baseline
- pipeline DAG

## Rejection Rules

- Reject ML demos with no data validation.
- Reject pipelines that cannot run locally.
- Reject streaming claims without message-rate benchmark.

## Reuse Priority

1. Use repo-local `.codex/skills/` and `.claude/skills/`.
2. Use `.portfolio/` and upstream `portfolio-reuse-kit`.
3. Use external repositories as references for organization, workflow, schemas, tests, benchmarks, and docs.
4. Use external code only with license compatibility, attribution, and a decision record.
