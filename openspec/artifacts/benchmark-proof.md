# Benchmark Proof: model-drift-detector

## Primary Metric

- Metric: `drift_alarm_f1`
- Unit: `ratio`
- Result: drift_alarm_f1 = pending
- Result path: `benchmarks/results/summary.json`

## Command

    ./tools/benchmark.ps1 -Rows 2000 -Repetitions 3 -HardwareClass desktop-docker

## Evidence

The corrected non-root default image must complete three source-locked repetitions.

The README/post number must come from the committed benchmark JSON, not from manual text.
