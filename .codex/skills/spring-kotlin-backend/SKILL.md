---
name: spring-kotlin-backend
description: Apply the Spring Kotlin backend stack profile, including MVC vs WebFlux, persistence choice, hexagonal/clean/modular organization, Testcontainers, observability, and k6 benchmark rules.
---

# Spring Kotlin Backend

Use this skill when `decision_brain.stack_profile` is `spring-kotlin-backend`.

1. Read `language-profiles/spring-kotlin.yaml` or `.portfolio/language-profiles/spring-kotlin.yaml`.
2. Choose Spring MVC by default for transactional REST APIs with blocking persistence.
3. Choose WebFlux only when the app is non-blocking end to end and the benchmark needs that behavior.
4. Choose Spring Data JDBC by default for explicit persistence; use JPA only when ORM mapping is part of the proof; use R2DBC only with WebFlux end to end.
5. For Spring Boot 4, use Jackson 3 coordinates (`tools.jackson.module:jackson-module-kotlin`) and the modular `spring-boot-starter-flyway`; do not inherit Boot 3 dependency coordinates by habit.
6. Bind PostgreSQL `timestamptz` values explicitly when the JDBC driver cannot infer `Instant`; UTC `OffsetDateTime` is the preferred adapter representation.
7. Organize packages so domain/application do not depend on adapters or framework code, and enforce the rule with an architecture test.
8. Add Testcontainers for PostgreSQL, Redis, RabbitMQ, Kafka/Redpanda, or other external services used by tests.
9. Add Actuator and Micrometer when observability or production readiness is part of the claim.
10. Add k6 benchmark for HTTP p95/p99 and failure benchmark for outbox/saga/broker projects. Exclude setup traffic from measured throughput and add p99 to `summaryTrendStats` before reading `p(99)` in a custom summary.
11. Commit Gradle wrappers for Windows and POSIX, the wrapper JAR/properties, and the official distribution checksum. Keep Docker as the universal execution path.

Rule: Spring Kotlin repos must show Kotlin fluency plus backend architecture, not just generated Spring code.
