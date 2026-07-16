# Technical Decision: model-drift-detector

## Runtime

- Python 3.12.13 slim image pinned by OCI digest.
- Non-root UID 10001.
- CPU-only execution.
- No runtime network, secret, database, broker, or cloud dependency.

The final dependency freeze and image metadata remain a release gate because Docker execution is currently unavailable.

## Libraries

| Library | Decision |
|---|---|
| NumPy 2.5.1 | Deterministic PCG64-backed scenario arrays and percentile aggregation. |
| SciPy 1.18.0 | Primary two-sided `ks_2samp` implementation. |
| Pydantic 2.13.4 | Strict manifest fields, bounded strings and sizes, role/type checks, and unknown-field rejection. |
| prometheus-client 0.25.0 | Official counters, gauges, and histogram with bounded labels. |
| Evidently | Rejected as a core dependency; optional future comparison/reporting adapter only. |

Direct dependencies are exact. Transitive versions must be frozen from the successful Docker build before publication.

## Why KS Plus Holm Plus Effect

KS works on continuous two-sample distributions and returns both p-value and a bounded maximum CDF difference. P-values alone become noisy with many columns and large batches. Holm controls family-wise error without assuming independent tests. A minimum KS effect of 0.10 prevents statistically significant but operationally tiny differences from becoming drifted columns.

The operational policy remains a domain decision rather than a SciPy default.

## Artifact Security And Integrity

- Manifest maximum: 1 MiB.
- Payload maximum: 64 MiB.
- Row maximum: 1,000,000.
- Payload name must be a basename.
- Resolved payload parent must equal the resolved manifest directory.
- Byte count and SHA-256 are verified before decoding.
- UTF-8, exact header/order, row count, numeric values, nullability, finiteness, roles, and minimum samples are enforced.
- Runtime network access is unnecessary.

## Telemetry

Metrics use only one bounded `outcome=alarm|stable` label. Batch IDs, feature names, values, model versions, and arbitrary exceptions are not metric labels. The CLI owns JSON detail; Prometheus owns aggregate operational state.

## API, Messaging, Storage, And Cloud

- API style: CLI because file batches are the unit of work.
- GraphQL: rejected; there is no client-selected graph.
- REST/gRPC: rejected until a remote protocol is measured.
- Kafka/RabbitMQ/NATS: rejected; no stream or delivery proof.
- Database: none; results are immutable files.
- Kumo/AWS: none; no cloud behavior exists.
- Airflow/MLflow: not duplicated; #21 owns lifecycle orchestration and registry.

## Benchmark Protocol

1. Generate one fixed reference batch and 22 current batches with independent seeds.
2. Serialize every batch to the shared manifest + CSV contract.
3. Reload all artifacts through path, size, row, schema, and SHA verification.
4. Run one stable warm-up evaluation.
5. Measure only statistical comparison plus alarm policy for every scenario.
6. Score all 20 supported scenarios; report two unsupported correlation-only scenarios separately.
7. Record complete scenario and per-column evidence, environment, versions, failures, and telemetry proof.
8. Repeat the complete Docker benchmark three times and aggregate without selecting the fastest run.

## Failure Policy

Any invalid artifact, unsupported format, schema mismatch, undersized batch, non-finite value, benchmark exception, or failed threshold exits nonzero and writes failure JSON. Failed runs must remain visible.

## Cross-Platform Rule

All product and validation behavior runs through Python, Docker, GitHub Actions, or PowerShell Core scripts supplied by the kit. No user-specific path or shell-only host dependency enters the product contract.
