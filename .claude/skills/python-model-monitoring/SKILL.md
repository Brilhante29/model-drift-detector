+---
name: python-model-monitoring
description: Design, implement, or audit Python model-monitoring and drift-detection repositories. Use for monitoring-batch contracts, model and dataset identity, data or prediction drift, labeled drift scenarios, statistical correction, effect thresholds, Prometheus telemetry, and reproducible benchmark evidence.
---

# Python Model Monitoring

Prove artifact integrity and alarm quality before adding orchestration or dashboards.

## Workflow

1. Define the monitored claim precisely: data drift, prediction drift, or labeled model-performance decay. Never treat one as evidence for another.
2. Accept immutable, versioned monitoring artifacts. Verify size, path containment, schema, byte count, SHA-256, producer, dataset, contract, model version, model artifact, capture time, and feature schema before parsing.
3. Reject comparisons across incompatible producers, contracts, models, or feature schemas. Reject the same artifact and reverse-time comparisons.
4. Keep alarm policy independent from SciPy, Evidently, telemetry, transport, storage, cloud, and orchestration. Put statistical engines and exporters behind narrow application ports.
5. Predefine deterministic stable and shifted scenarios. Separate supported scenarios from documented blind spots.
6. Apply an explicit multiple-test correction and minimum effect threshold. Record p-values, adjusted thresholds, effects, drifted columns, and final policy inputs.
7. Publish at least three same-image repetitions with F1, precision, recall, false-positive rate, runtime samples, failures, workload identity, source/image/wheel/lock digests, and a comparability key.

## Stack Rules

- Default local-first profile: pinned Python, NumPy, SciPy, Pydantic, JSON Schema, Prometheus client, Docker, pytest, Ruff, and a transitive lock.
- Use Evidently as a replaceable reporting or comparison adapter only when its added surface is measured.
- Add FastAPI, GraphQL, gRPC, Kafka, RabbitMQ, Airflow, MLflow, Kumo, or cloud services only when the acceptance criteria require that boundary.
- Never auto-retrain from a drift alarm. Emit evidence for investigation and let lifecycle orchestration own promotion.

## Required Evidence

- Labeled stable and shifted scenarios with truth fixed before detection.
- Alarm F1, precision, recall, false-positive rate, and runtime distribution.
- Explicit unsupported scenarios or blind spots.
- Tamper, path escape, schema mismatch, model mismatch, and time-order rejection tests.
- Non-root, credential-free Docker execution with exact dependencies and no runtime network.
- README number derived from committed Benchmark Result V2 evidence.

## Reuse Boundary

Share artifact schemas, identity compatibility rules, benchmark contracts, statistical decision guidance, and publication gates. Keep fixture seeds, shift magnitudes, monitored features, policy thresholds, Prometheus names, and detector implementation local until another project proves a stable abstraction.

