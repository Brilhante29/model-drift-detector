# Spec: model-drift-detector

## Number

#22

## Claim

One local-first Docker command verifies immutable monitoring batches, detects supported univariate feature and prediction drift with auditable statistics, and measures alarm quality against labeled deterministic scenarios.

## Problem

#21 can move a model to production, but a viable portfolio system also needs evidence about whether deployed inputs and outputs remain familiar. The monitor must avoid three common false claims: equating drift with accuracy loss, using p-values without effect control, and presenting an attractive report without labeled alarm evaluation.

## Users

- An ML engineer validating post-deployment monitoring policy.
- A platform engineer integrating a producer with the shared monitoring-batch contract.
- A reviewer checking statistical decisions, false positives, and reproducibility.

## Inputs

- A version 1 `monitoring-batch.manifest.json`.
- One CSV payload inside the same directory.
- At least 200 rows.
- Numeric, non-null feature and prediction columns.
- Matching reference/current columns, order, and roles.

The manifest records bytes and SHA-256. The consumer verifies both before CSV parsing.

## Outputs

- A typed decision JSON with batch alarm, feature drift share, prediction state, per-column p-values, KS effects, adjusted alpha, and drifted columns.
- A Prometheus text snapshot with bounded outcome, alarm, drifted-column count, and duration metrics.
- A portfolio benchmark JSON with F1, precision, recall, false-positive rate, p50/p95, scenario matrix, environment, thresholds, and failures.

## Statistical Policy

1. Compute a two-sided two-sample KS test per monitored numeric column.
2. Apply Holm sequential correction with family alpha 0.05.
3. Require KS effect at least 0.10 in addition to adjusted significance.
4. Alarm when feature drift share reaches 0.125 or any prediction column drifts.
5. Refuse undersized, non-finite, or schema-mismatched batches.

## Scenario Matrix

- 8 stable seeds, scored negative.
- 4 mean-shift seeds, scored positive.
- 4 scale-shift seeds, scored positive.
- 4 prediction-shift seeds, scored positive.
- 2 correlation-only seeds, positive but unscored and reported as a known blind spot.

Scenario truth and seeds are defined before the detector runs. Correlation-only drift is excluded from primary scoring because the claim is explicitly univariate.

## In Scope

- Immutable local artifact validation.
- Data and prediction drift proxies.
- Auditable policy and detector substitution.
- Prometheus-compatible operational metrics.
- Deterministic Docker benchmark.

## Out Of Scope

- Concept drift or performance decay without labels.
- Automatic retraining or rollback.
- Streaming, alert routing, dashboard hosting, or model registry.
- Online HTTP, GraphQL, gRPC, or WebSocket APIs.
- Cloud services and credentials.
- Multivariate dependency-shift detection.

## Acceptance Criteria

- Default Docker command runs without network or secrets.
- Tampered, escaping, malformed, oversized, or mismatched artifacts fail closed.
- Domain and application code import no statistical, validation, telemetry, orchestration, transport, or cloud framework.
- Stable and shifted scenario truth is preserved in result JSON.
- F1 and false-positive rate are computed from all scored scenarios.
- The correlation-only blind spot remains visible.
- Tests cover policy, adapters, artifact integrity, telemetry, CLI, benchmark, and architecture.
- README number is copied only from current committed Docker evidence.

## Definition Of Done

The project is implemented but not publishable until the pinned image builds, exact dependencies are frozen, container lint/tests/coverage pass, three full runs are preserved, summary and README agree, strict validation passes, and public CI is green.
