# Architecture Decision: model-drift-detector

## Status

Accepted; publication evidence is being regenerated after a runtime-path correction.

## Dominant Forces

- Ordered data and evidence transformations.
- High reproducibility and auditability.
- Medium statistical domain complexity.
- Replaceable statistical and telemetry adapters.
- No UI, persistence, asynchronous throughput, or independent deployability pressure.

## Decision

Use a pipeline architecture with two narrow inward-facing ports:

```text
manifest -> integrity/schema -> batch -> statistical evidence
         -> Holm/effect policy -> decision -> CLI/Prometheus -> benchmark
```

`MonitoringBatch`, `ColumnStatistic`, `AlarmPolicy`, and `DriftDecision` are immutable domain values. `DriftMonitor` depends on statistical and telemetry behavior. SciPy, Pydantic, Prometheus, fixture I/O, benchmark orchestration, and CLI are adapters.

## Why Pipeline

The central complexity is transition correctness: no parsing before integrity, no alarm before evidence correction, no metric before a decision, and no portfolio claim before scenario scoring. A pipeline makes these order constraints visible.

## SOLID And Coupling

- **SRP:** artifact, detector, policy, telemetry, fixture, benchmark, and CLI each own one reason to change.
- **OCP:** a Wasserstein, PSI, Evidently, or multivariate detector can implement the statistical port without rewriting policy or CLI.
- **LSP:** a replacement detector must return the same bounded per-column evidence and reject unsupported inputs rather than silently changing semantics.
- **ISP:** detector and telemetry protocols expose one operation each.
- **DIP:** application policy depends on `ColumnStatistic` behavior, not SciPy or Evidently.
- **KISS:** one transparent KS method and one correction are easier to audit than automatic method selection.
- **YAGNI:** API servers, brokers, Airflow, MLflow, cloud, dashboards, and retraining do not improve the benchmark.
- **DRY:** artifact and benchmark contracts live in the reuse kit; project-specific statistical code remains local.

The dependency test rejects SciPy, NumPy, Pydantic, Prometheus, Evidently, Airflow, MLflow, FastAPI, and cloud SDK imports from domain/application modules.

## Rejected Alternatives

### MVC Or Layered Controller-Service-Repository

There is no UI controller or persistence repository. These layers would obscure the evidence pipeline and invent database boundaries.

### Hexagonal As The Primary Label

Ports are useful for detector and telemetry substitution, but external actors do not dominate the system. Pipeline better describes the ordered transformations.

### Event-Driven Or Microservices

No stream, fan-out, queue durability, independent scaling, ownership split, or release cadence is measured. Network boundaries would weaken reproducibility.

### Evidently As The Core

Evidently provides useful reports and many methods, but automatic defaults would own the statistical claim. It remains a possible reporting/comparison adapter.

## OpenSpec Self-Challenge

| Question | Answer |
|---|---|
| What problem force dominates? | Ordered, reproducible, auditable evidence transformation. |
| Could the policy be a single SciPy function? | No. Statistical evidence and operational alarm semantics change for different reasons and need separate tests. |
| Are ports ceremonial? | Detector substitution and telemetry isolation are exercised with test doubles; no other ports were added. |
| Does one feature drift justify an alarm? | For the fixed eight-feature contract, 0.125 means one feature; the exact policy is recorded and benchmarked rather than hidden. |
| Does drift prove accuracy loss? | No. The public output explicitly states that ground-truth model performance is unavailable. |
| What is not detected? | Correlation-only multivariate drift; two unscored scenarios preserve this limitation. |
| What would invalidate this architecture? | A measured online latency, streaming, label-join, or multivariate requirement that changes the dominant flow. |

## Revisit Triggers

- Add delayed-label performance monitoring only when target artifacts exist.
- Add multivariate detection only with a labeled scenario benchmark and explicit false-positive budget.
- Add a service only when repeated remote clients and protocol latency become acceptance criteria.
- Add streaming only after a message-rate, windowing, and delivery guarantee is specified.
- Add cloud only when concrete AWS behavior is required; use Kumo before real AWS.
