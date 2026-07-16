# #22 model-drift-detector

**Benchmark:** `drift_alarm_f1` is pending the immutable Docker run; no local preview number is presented as publication evidence.

**Proves:** an auditable post-deployment monitor can reject tampered batches, distinguish data and prediction drift from model-performance claims, control multiple tests, and score its alarm policy against deterministic scenario truth.

## Run

```bash
docker build -t model-drift-detector .
docker run --rm model-drift-detector
```

The default command needs no network, secret, paid API, database, broker, or cloud account at runtime. It writes and prints a portfolio benchmark result.

## Benchmark

| Metric | Value | Unit | Meaning |
|---|---:|---|---|
| Alarm F1 | pending | ratio | balance of alarm precision and recall |
| False-positive rate | pending | ratio | stable scenarios incorrectly alarmed |
| Detection p95 | pending | ms | statistical comparison plus policy |
| Blind-spot detection | pending | ratio | correlation-only scenarios, outside the supported univariate claim |

Publication requires three complete Docker runs on one pinned image, all raw results, the median summary, image ID, environment, and zero hidden failures.

## What It Monitors

- **Data drift:** a feature distribution changed.
- **Prediction drift:** the model output distribution changed.
- **Not claimed without labels:** concept drift, accuracy decay, or model-performance drift.

An alarm is an investigation signal. It is not proof that model quality degraded.

## Decision Rule

Each numeric feature and prediction column receives a two-sided Kolmogorov-Smirnov p-value and KS effect size. Holm correction controls family-wise error across columns. A column drifts only when adjusted significance and `KS >= 0.10` both hold. The batch alarms when at least one of eight features drifts or prediction drift is present.

The fixed benchmark contains eight stable scenarios, four mean shifts, four scale shifts, four prediction shifts, and two unscored correlation-only scenarios that document the univariate detector's blind spot.

## Artifact Contract

`monitoring-batch.manifest.json` records producer, model version, capture time, column roles, payload format, rows, bytes, and SHA-256. The consumer:

1. resolves the payload inside the manifest directory;
2. rejects path escape, oversized files, unknown fields, duplicate columns, nulls, and non-finite values;
3. verifies bytes and SHA-256 before parsing;
4. requires exact CSV column order and row count.

The shared schema lives at [`monitoring-batch.schema.json`](.portfolio/contracts/monitoring-batch.schema.json).

## Detect Two Batches

```bash
model-drift-detector validate path/to/monitoring-batch.manifest.json
model-drift-detector detect reference/monitoring-batch.manifest.json current/monitoring-batch.manifest.json
```

## Architecture

```mermaid
flowchart LR
    A[Manifest + payload] --> B[Integrity and schema adapter]
    B --> C[Immutable monitoring batch]
    C --> D[SciPy KS adapter]
    D --> E[Holm correction + alarm policy]
    E --> F[CLI decision JSON]
    E --> G[Prometheus metrics]
    H[Labeled scenario harness] --> A
    F --> I[Benchmark F1, FPR, p50, p95]
```

The architecture is a pipeline because ordered evidence transformations dominate the problem. Narrow detector and telemetry ports preserve DIP and LSP without pretending the project needs a distributed clean-architecture framework.

## Portfolio System

| Repository | Responsibility | Shared boundary |
|---|---|---|
| #21 `mlops-end2end` | validate, train, register, promote, and serve | model identity and inference lifecycle |
| #22 `model-drift-detector` | inspect deployed feature and prediction batches | monitoring-batch manifest |
| #23 `feature-store-lite` | serve governed features | feature names, types, and freshness |
| #26 `data-quality-checks` | reject invalid source rows | data-contract failures before monitoring |

#22 does not import #21 code. Any producer can satisfy the versioned artifact contract.

## Engineering Proof

- Domain and application modules import no SciPy, Pydantic, Prometheus, Airflow, MLflow, Evidently, FastAPI, or cloud SDK.
- Statistical, artifact, policy, telemetry, fixture, and CLI behavior have focused tests.
- Docker uses a non-root user and a Python base pinned by tag and OCI digest.
- OpenSpec records intent, architecture self-challenge, reuse delta, benchmark questions, and release verification.
- Benchmark evidence is explicitly `pending` until the final container and protocol are frozen.

## Local Development

```bash
python -m pip install -e ".[dev]"
pytest
ruff check src tests
```

The supported publication path is Docker. Host Python runs are development feedback only.

## References

See [REFERENCES.md](REFERENCES.md) for primary statistical, runtime, telemetry, and organization sources.
