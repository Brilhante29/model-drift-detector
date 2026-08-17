# Design: ship model-drift-detector

## Flow

```text
manifest + CSV
  -> resolve and verify size/SHA
  -> parse exact numeric schema
  -> SciPy KS evidence
  -> Holm correction + minimum effect
  -> feature/prediction alarm policy
  -> CLI JSON + Prometheus
  -> labeled benchmark score
```

## Boundaries

- Domain: immutable batches, statistics, decisions, and policy.
- Application: detector and telemetry protocols.
- Adapters: Pydantic/artifact I/O, SciPy, Prometheus, fixtures, benchmark, and CLI.

## Invariants

- Integrity precedes parsing.
- Reference/current schema and roles match.
- P-value and effect are both required.
- Multiple tests are corrected as one family.
- Drift remains a proxy without labels.
- Scenario truth is not available to detector code.
- Evidence is current only while source-locked workload and dependency inputs remain unchanged.

## Rejected Complexity

No HTTP/GraphQL/gRPC, broker, stream processor, registry, database, Airflow, MLflow, cloud, Kumo, dashboard, or automatic retraining enters this change.
