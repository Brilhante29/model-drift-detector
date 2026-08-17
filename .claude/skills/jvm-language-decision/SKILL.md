---
name: jvm-language-decision
description: Choose Java, Kotlin, or a mixed JVM boundary from problem forces, interoperability needs, and measurable evidence; use before creating or migrating any JVM portfolio repository.
---

# JVM Language Decision

1. Read `decision-brain/jvm-language-matrix.yaml`, `decision-brain/stack-matrix.yaml`, the project claim, architecture record, and benchmark plan.
2. Identify whether Java records/sealed interfaces/virtual threads, Kotlin sealed states/null safety/value classes, or a mixed stable-core boundary changes the solution materially.
3. Reject a language migration that only adds a resume keyword or changes syntax without fixing the domain failure.
4. Keep framework types outside domain and use ports before adapters. For a mixed build, Java exposes stable nullability-aware contracts and Kotlin depends inward on them.
5. Require committed `gradlew`, `gradlew.bat`, wrapper JAR and properties, `build.gradle.kts`, `settings.gradle.kts`, explicit JVM toolchain, tests, Docker, and identical gates for Java and Kotlin.
6. Do not add coroutines unless suspending I/O is end-to-end. Do not compare Java and Kotlin performance unless workload and implementation variables are controlled.
7. Record selected language, rejected alternatives, interoperability boundary, wrapper version, and benchmark effect in `project.yaml` and `sdd/technical-decision.md`.
8. For the current portfolio, follow the explicit repository decisions in the matrix unless new evidence changes the problem forces.
