---
name: python-feature-store
description: Design, implement, or audit Python feature stores and Feast integrations. Use for point-in-time historical retrieval, offline-to-online materialization, FeatureService contracts, TTL behavior, feature ingestion manifests, online-read benchmarks, and decisions about Parquet, SQLite, Redis, APIs, or cloud providers.
---

# Python Feature Store

Build the smallest real feature-store path that proves temporal correctness before performance.

## Workflow

1. Define the measurable claim, entity, feature schema, event timestamps, TTL, query timestamps, and serving boundary.
2. Select a proven engine when registry, point-in-time join, materialization, or online-store semantics are part of the claim. Use pure Python only as an independent oracle, never as a substitute disguised as the engine.
3. Keep records, temporal truth, scoring, and use-case policy free of Feast, Pandas, PyArrow, storage SDKs, transports, and cloud code. Put engine behavior behind a narrow application port and test a fake for LSP-compatible behavior.
4. Ingest through a versioned manifest. Fail closed on unknown schema or contract IDs, failed quality status, digest mismatch, row reconciliation mismatch, and artifact paths escaping the manifest directory.
5. Define expected point-in-time vectors before engine retrieval. Include later source rows for eligible queries, explicit TTL-null cases, missing values, and at least one tamper test.
6. Materialize offline data into the online store, open a fresh reader, verify the first read separately, warm up, measure, and validate every timed response after stopping its timer.
7. Publish three same-image repetitions with the effective workload, all samples, p50/p95/p99, throughput, correctness metrics, source/image/wheel/lock digests, failures, and a comparability key.

## Stack Rules

- Default local-first profile: pinned Python, Feast, Parquet offline source, local registry, SQLite online store, Docker, pytest, Ruff, and a transitive lock.
- Add Redis only for a measured cross-process, concurrency, or network-serving hypothesis.
- Add FastAPI, GraphQL, or gRPC only when transport is part of the acceptance metric.
- Add Airflow or MLflow in lifecycle orchestration repositories, not in a focused storage/retrieval proof.
- Add Kumo or cloud adapters only when AWS behavior exists; keep provider SDKs outside domain and application policy.
- Treat transitive packages as dependencies, not architectural boundaries.

## Required Evidence

- Historical match rate `1.0` against the independent oracle.
- Future leak count `0` with future rows present in the fixture.
- TTL violation count `0` with expected null cases present.
- Online value match rate `1.0` after materialization.
- Warmed online p50/p95/p99 and entity-value throughput; report first read and materialization separately.
- Non-root, credential-free Docker execution with exact dependencies and no runtime network.
- Current README number derived from committed Benchmark Result V2 evidence.

## Reuse Boundary

Share manifest schemas, benchmark contracts, validation rules, and adapter-selection decisions. Keep entity formulas, temporal fixtures, FeatureService names, feature definitions, and domain-specific aggregation in the project until another implementation proves a stable abstraction.
