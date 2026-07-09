# #22 model-drift-detector

**Status:** scaffold

**Proves:** deteccao de drift.

**Benchmark target:** drift_alarm_vs_baseline.

**Stack:** python, pandas, scipy, prometheus, docker.

## Next milestone

Implement the smallest Docker-runnable version and produce the first JSON benchmark under enchmarks/results/.

## Run

`ash
docker build -t model-drift-detector .
docker run --rm model-drift-detector
`

## Benchmark

`ash
docker run --rm model-drift-detector benchmark
`

| Metric | Value | Unit |
|---|---:|---|
| drift_alarm_vs_baseline | pending | pending |

## Architecture

Defined in sdd/spec.md before implementation.

## References

See REFERENCES.md.