---
name: python-computer-vision
description: Design, implement, benchmark, and publish reproducible Python computer-vision repositories for training, evaluation, model artifacts, OCR, or serving. Use when a project involves images, detection, classification, Ultralytics, PyTorch, OpenCV, Pillow, model checkpoints, mAP, AUC, per-image latency, or inference throughput.
---

# Python Computer Vision

## Decide From The Claim

1. State the image task, data source, primary metric and public limitation before choosing a model.
2. Use a pipeline for dataset -> training -> evaluation -> artifact flows. Use a modular monolith for one serving process. Add ports only around real substitutions such as model runtime or artifact storage.
3. Keep API, registry, orchestration, export and GPU comparison in separate repositories unless they are required by the measured claim.

## Protect Data And Evaluation

1. Version dataset source, license, checksum, class map, dimensions, split counts and preprocessing identity.
2. Verify annotation bounds, split disjointness and content hashes before training.
3. Evaluate only on the declared held-out split. Never turn training metrics into public quality claims.
4. Treat a synthetic fixture as pipeline evidence only. State that it does not prove real-domain generalization.

## Publish Model Artifacts

1. Emit checkpoint plus a schema-versioned manifest containing byte count, SHA-256, framework/version, architecture, input contract, classes, provenance and held-out metrics.
2. Verify manifest schema, bytes and SHA-256 before any consumer loads the framework artifact.
3. Keep framework-specific loaders in adapters; pure annotation, aggregation and artifact policy must not import model or transport frameworks.

## Benchmark Honestly

1. Fix seed, device, thread count, image size, batch, warmup, measured samples and concurrency.
2. Reload the persisted best checkpoint before inference timing.
3. Report quality and cost together: mAP/AUC/accuracy as appropriate, p50/p95 latency, throughput, training duration and artifact size.
4. Preserve raw runs and failures. Aggregate only runs with the same workload and comparability key.
5. Generate V2 evidence from a clean source commit and immutable OCI image; bind fixture, config, dependency lock and raw-result digests.

## Runtime And License Gates

1. Make pinned Docker the default local-first path with no credential, dataset download or mutable weight download at runtime.
2. Use CPU by default for universal CI. Treat GPU as a separate hardware profile and comparability key.
3. Record framework, weights, dataset, annotation and generated-asset licenses. Align repository licensing with imported runtimes such as Ultralytics.
4. Reject cloud, broker, database and cache components unless their behavior is part of the proof. Use Kumo behind a storage port only when AWS-like behavior exists.

## Required Output

Keep `project.yaml`, README, SDD, OpenSpec, raw benchmark JSON, V2 publication evidence, tests, Docker and GitHub Actions aligned. The README must open with the measured number and the exact scope it proves.
