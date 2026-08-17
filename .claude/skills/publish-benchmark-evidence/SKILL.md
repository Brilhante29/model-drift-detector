---
name: publish-benchmark-evidence
description: Generate or review reproducible benchmark-result-v2 publication evidence for a portfolio repository. Use when a project has a real benchmark result and needs provenance, workload sizing, comparability, README alignment, exact-head CI proof, or a decision between the generic producer and a project-specific multi-run producer.
---

# Publish Benchmark Evidence

Create publication evidence from a real execution. Never convert documentation or an old number into a benchmark result.

## Choose The Producer

1. Use tools/generate-publication-benchmark.py when one command emits a V1 metric/value result and one aggregation policy is sufficient.
2. Keep a project-specific producer when the claim needs multiple independent runs, multiple metrics, domain-specific aggregation, provider diagnostics, or extra provenance.
3. Reuse the V2 schema and publication verifier in both cases. Do not force project semantics into the generic tool.

## Execute

1. Require a clean Git tree, pinned dependencies, a pinned Docker image, fixture/config inputs, and a declared comparability key.
2. Hash tracked fixture, config, and lock inputs from Git blobs at `provenance.source_commit`, never from checkout bytes. This makes evidence invariant to CRLF/LF conversion. Hash the generated raw result from the bytes actually produced.
3. Ensure CI fetches enough history to contain `provenance.source_commit`; a shallow checkout must not silently weaken provenance.
4. Determine the measured workload count from explicit V1 count fields or pass --measured-iterations. Never derive measured iterations from repeat.
5. Run the benchmark. Preserve the raw result and emit benchmarks/publication/<name>-v2.json.
6. Validate the V2 file against .portfolio/contracts/benchmark-result-v2.schema.json or the kit contract.
7. Align the README opening, project.yaml, SDD, and OpenSpec with the committed value.
8. Commit raw evidence and V2 evidence, push without force, then verify CI for that exact SHA with tools/verify-github-publication.ps1.

Generic producer shape:

    python tools/generate-publication-benchmark.py
      --repo .
      --project <name>
      --benchmark-id <stable-id>
      --image <pinned-local-tag>
      --v1-result benchmarks/results/<raw>.json
      --fixture <fixture-path>
      --config <config-path>
      --lock <lock-path>
      --output benchmarks/publication/<name>-v2.json
      --measured-iterations <work-items>
      --direction <direction>
      --runtime <runtime>
      --comparability-key <stable-key>
      -- <benchmark-command>

Use --from-container <name>:<path> when a non-root container cannot write a host bind mount. Set --timeout-seconds for the workload; the producer must not wait indefinitely on a server command.

## Integrity Gates

Reject publication when any condition is true:

- the tree was dirty before execution;
- the source SHA, image digest, dependency digest, fixture digest, or config digest is missing;
- workload count is absent or ambiguous;
- the result has only a schema pass but contradicts raw evidence;
- README numbers do not match the committed result;
- CI success is not tied to the exact evidence commit.

A schema-valid artifact can still be semantically false. Inspect workload size, aggregation, samples, units, provider mode, and comparability key.

## Handoff

Record the source SHA, artifact SHA, benchmark command, raw paths, V2 path, metrics, CI run URL, known limitations, and the next exact action. Do not persist credentials or private chain-of-thought.