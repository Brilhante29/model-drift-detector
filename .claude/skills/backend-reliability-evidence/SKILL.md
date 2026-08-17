---
name: backend-reliability-evidence
description: Build or audit backend reliability repositories that claim transactions, event sourcing, sagas, outbox delivery, caching, consistency, or failure recovery. Use when Claude must replace in-memory simulations with real local infrastructure, connect repositories through versioned contracts, or publish reproducible failure benchmarks without false production claims.
---

# Backend Reliability Evidence

## Workflow

1. Read `project.yaml`, SDD, README, code, Docker path, CI, and current benchmark JSON.
2. Trace every public claim to an implementation and measured workload. Mark absent infrastructure, no-op compensation, prewritten JSON, and tautological metrics as blockers.
3. Select the smallest topology that proves the invariant. Do not add a broker, cloud emulator, microservice, or ORM unless the failure mode needs it.
4. Put domain rules behind narrow ports. Keep Spring, JDBC, Redis, Kafka, HTTP, and cloud SDK imports outside domain and use-case packages.
5. Exercise the real failure boundary through Docker. Generate the benchmark artifact during the run and export it through a host volume or CI artifact.
6. Publish benchmark result V2 with at least three measured repetitions, warm-up, workload digests, exact commit/image provenance, samples, failures, and comparability key.
7. Update README, SDD, handoff, reuse review, and limits from the measured result. Never preserve a stronger claim than the workload proves.

## Pattern Gates

- **Payments:** prove atomic idempotency and state transitions with real PostgreSQL locking/constraints.
- **Event sourcing:** prove durable append, aggregate sequence uniqueness, optimistic concurrency, restart replay, and projection rebuild.
- **Saga:** execute stateful operations and reverse them idempotently; a failed compensation ends `FAILED`, never `COMPENSATED`.
- **Outbox:** commit business row and event atomically; test crash after commit, publish retry, competing workers, loss, duplicates, and lag.
- **Cache:** use real source-of-truth and cache adapters; report hit ratio, p95/p99, throughput, and stale-value failures without claiming dual-write atomicity.

## Program Contract

- Use the vendored `commerce-event-v1` envelope for asynchronous cross-repository edges.
- Version synchronous provider contracts and pin them in consumers.
- Keep each repository's database private.
- Reuse correlation/idempotency identifiers across retries.
- Prefer a local adapter for tests and a real local infrastructure adapter for measured evidence; require parity through the same port.

## Release Rejections

Reject publication when `.gradle` or build caches are tracked, the wrapper is incomplete, `gradlew` is not tracked as mode `100755`, the default run needs a paid secret, a CI smoke run overwrites committed publication evidence, the benchmark file predates the run, README omits the primary number, CI does not test the exact head, or documentation names infrastructure absent from the measured path.
