---
name: kafka-streams
description: "Decide and design simple Kafka consumers or Kafka Streams topologies from problem forces, then define keys, schemas, state, failures, restoration, tests, and reproducible broker evidence. Use for Kafka consumer, stream processing, joins, windows, state stores, replay, rebalance, retry/DLQ, or Kafka benchmark work."
---

# Kafka Streams

1. Read `decision-brain/messaging-matrix.yaml`, `decision-brain/kafka-streams-matrix.yaml`, `docs/kafka-streams-decision.md`, and the applicable JVM language profile. Use `.portfolio/` copies inside generated repositories.
2. State the invariant that requires asynchronous records. Reject Kafka when a synchronous call, database transaction, outbox-only worker, or simpler queue solves it. Never add Kafka for resume padding.
3. Choose a simple consumer for independent per-record commands, manual batching, offset control, or external-state workflows. Choose Kafka Streams only for a justified topology, keyed state, join, aggregation, window, table, materialized view, or replay-built state.
4. Record problem forces, rejected alternatives, topics, key, partitioning, ordering scope, null keys, hot-key risk, and every required matrix field in `project.yaml` and `sdd/technical-decision.md`.
5. Define key and value SerDes, schema compatibility, tombstones, invalid-record categories, and state-store migration or rebuild behavior. Prohibit silent drops.
6. Define stream/table semantics, joins, event time, timestamp extraction, window, grace, retention, suppression, stores, changelogs, and repartition topics before implementation.
7. Use at-least-once by default with idempotent business effects. Select exactly-once-v2 only for Kafka-contained read-process-write results; never extend that claim to HTTP, database, or other external side effects.
8. Classify transient and permanent failures. Bound retry attempts and elapsed time, preserve ordering requirements, attach source metadata to quarantine or DLQ records, and make replay observable and idempotent.
9. Test topology semantics with `TopologyTestDriver`. Use Testcontainers with a real Kafka-compatible broker for broker persistence, serialization, transactions, restart, restoration, replay, rebalance, lag, throughput, and availability claims.
10. Require Gradle Wrapper, Kotlin DSL, aligned JVM toolchains, clean-clone checks, and Docker builds that run tests. Apply `language-profiles/kotlin-jvm.yaml` for non-Spring Kotlin or `language-profiles/java-spring.yaml` for Java Spring.
11. Make correctness gates fail before measuring performance. Separate driver microbenchmarks from real-broker benchmarks and retain raw samples, environment, workload, warmup, repetitions, commit, dirty flag, and image digest.
12. Reject publication if records are silently lost, output invariants fail, external effects are called exactly-once without proof, or a broker claim lacks a real-broker failure test.
