# Reuse Improvement Review: model-drift-detector

## Trigger

Implementing #22 exposed that the reuse kit named drift only as a vague `drift_alarm_delta` metric. It had no portable producer/consumer artifact, no skill separating drift proxies from labeled model performance, and no gate for multiple-test or effect-size decisions.

## What Belongs In The Kit

- `contracts/monitoring-batch.schema.json` for producer/consumer interoperability.
- `python-model-monitoring` skills for Codex and Claude.
- `docs/model-monitoring.md` for claim boundaries and evidence ordering.
- MLOps component-pack updates for F1, false positives, immutable batch manifests, and scenario matrices.
- Installer and kit validator support for the shared contract and skills.
- A future explicit `monitoring_batch` section in the project schema/template and semantic project validator.

## What Stays Local

- Exact KS detector implementation.
- Eight-feature fixture and shift magnitudes.
- 0.125 feature-share threshold.
- CLI commands and JSON shape beyond the shared benchmark contract.
- Prometheus metric names.
- Scenario seeds and correlation-only blind spot.
- Benchmark execution and result files.

These are implementation choices for #22, not universal portfolio defaults.

## OpenSpec Self-Challenge

| Question | Answer |
|---|---|
| Is a shared artifact justified before two producers exist? | Yes. #21, #23, and #26 already need the same identity, schema, integrity, and row metadata; #22 is the first strict consumer. |
| Is the skill too SciPy-specific? | No. It requires evidence/effect/correction/policy separation and treats SciPy/Evidently as replaceable adapters. |
| Did the kit absorb project code? | No. It absorbed contract and decision rules only. |
| Is JSON Schema enough? | Not yet. Project manifests should also declare producer/consumer role and validators should require hash-before-read evidence. |
| Did the benchmark reveal a reusable gap? | Yes. Drift proof needs labeled stable and shifted scenarios, F1/FPR, and an explicit blind spot, not only a drift score. |

## Applied Patches

- [x] Add monitoring-batch JSON Schema.
- [x] Copy the schema into generated project standards.
- [x] Add mirrored model-monitoring skills to the proving project for promotion.
- [x] Add model-monitoring documentation.
- [x] Update MLOps pack skills, metrics, and preferred artifacts.
- [x] Validate all new reusable files and patterns.
- [x] Add explicit `monitoring_batch` semantics to project schema and validator.
- [ ] Publish the kit and synchronize the exact commit into #22.

## Final Gate

- [x] Reusable improvements were patched or recorded.
- [x] Project-specific implementation was not moved into the kit.
- [x] Validation reflects monitoring artifact integrity and declaration semantics.

## Verdict

The implementation-stage reuse review is `patch-required-and-applied` locally. Runtime tests and lint pass in Docker; canonical three-run evidence and reuse-kit promotion remain release gates.
