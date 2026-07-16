# Architecture Record: model-drift-detector

## Decision

- Architecture: `pipeline`
- Stack profile: `python-ml`
- API style: `cli`
- Messaging: `none`
- Database/runtime: `none` / `Single non-root Python 3.12.13 container pinned by OCI digest; CPU-only deterministic benchmark with no network or credentials at runtime.`

## Reason

The dominant force is an ordered evidence flow: verify artifacts, parse batches, compute statistics, correct hypotheses, apply alarm policy, emit telemetry, and score decisions.

## Dependency Direction

Artifact, SciPy, telemetry, and CLI adapters depend on domain values and application protocols; the domain never depends on an external framework.

## Boundaries

- immutable monitoring-batch artifact and integrity verification
- numeric batch domain values
- SciPy two-sample KS adapter
- Holm correction and alarm policy
- Prometheus telemetry adapter
- deterministic scenario and benchmark orchestration
- file-oriented CLI

## Library Policy

NumPy generates deterministic fixtures, SciPy supplies the reviewed two-sample KS implementation, Pydantic rejects malformed manifests, and Prometheus exports bounded operational metrics. Evidently remains an optional comparison adapter because its defaults must not own the claim.

## Principle Check

- SRP: keep benchmark, API, use cases, and adapters separate.
- OCP: new providers must be adapters, not domain rewrites.
- LSP: replacement providers must preserve observable behavior.
- ISP: ports stay narrow.
- DIP: application depends on behavior, not infrastructure.
- KISS/YAGNI: leave out anything that does not improve the benchmark.
