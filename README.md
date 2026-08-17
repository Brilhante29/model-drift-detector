# #22 model-drift-detector

**Benchmark:** publication evidence pending for the source-locked Docker workload.

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
| Alarm F1 | pending | ratio | median across 3 pinned-image runs |
| False-positive rate | pending | ratio | stable scenarios incorrectly alarmed |
| Detection p95 | pending | ms | median comparison and policy tail |
| Blind-spot detection | pending | ratio | documented univariate correlation-only blind spot |

The publication harness requires a clean source commit, builds one image, runs three independent repetitions, preserves every metric sample, and emits both a readable summary and Benchmark Result V2 provenance.

## What It Monitors

- **Data drift:** a feature distribution changed.
- **Prediction drift:** the model output distribution changed.
- **Not claimed without labels:** concept drift, accuracy decay, or model-performance drift.

An alarm is an investigation signal. It is not proof that model quality degraded.

## Decision Rule

Each numeric feature and prediction column receives a two-sided Kolmogorov-Smirnov p-value and KS effect size. Holm correction controls family-wise error across columns. A column drifts only when adjusted significance and `KS >= 0.10` both hold. The batch alarms when at least one of eight features drifts or prediction drift is present.

The fixed benchmark contains eight stable scenarios, four mean shifts, four scale shifts, four prediction shifts, and two unscored correlation-only scenarios that document the univariate detector's blind spot.

## Artifact Contract

`monitoring-batch.manifest.json` records producer, model artifact identity, capture time, column roles, payload format, rows, bytes, and SHA-256. It also locks a successful upstream `validated-batch-manifest-v1`. The consumer:

1. resolves the payload inside the manifest directory;
2. rejects path escape, oversized files, unknown fields, duplicate columns, nulls, and non-finite values;
3. reconciles source, accepted, quarantine, and quality rows;
4. verifies every digest before parsing;
5. rejects incompatible producer, contract, model, time order, or feature schema;
6. requires exact CSV column order and row count.

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
- Benchmark publication is source locked: the V2 artifact must reference an ancestor commit whose lock and workload remain unchanged.

## Local Development

```bash
python -m pip install -c constraints.lock -e ".[dev]"
pytest
ruff check src tests
```

The supported publication path is Docker. Host Python runs are development feedback only.

## References

See [REFERENCES.md](REFERENCES.md) for primary statistical, runtime, telemetry, and organization sources.
