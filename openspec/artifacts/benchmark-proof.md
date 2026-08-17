# Benchmark Proof: model-drift-detector

## Primary Metric

- Metric: `drift_alarm_f1`
- Unit: `ratio`
- Result: drift_alarm_f1 = 1.0
- Result path: `benchmarks/results/summary.json`
- Publication path: `benchmarks/publication/model-drift-v2.json`

## Command

    ./tools/benchmark.ps1 -Rows 2000 -Repetitions 3 -HardwareClass desktop-docker

## Evidence

- Source commit: `12534946a5a6cb35e10260702d3765bc86b1931a`
- Image: `sha256:fe60560a0d32b9cb6319cc7de7783b13c0caa93f24b33b95fdd143a8593251ac`
- Wheel: `sha256:448368c4cea6a39597e8e97111865c5d6712c62c5a5359e746f65e685ae96e77`
- Fixture: `sha256:b412010a3de9e8dc0a98292f7a122fb33edb2e98b6e51cbbfdd40edb625c0cf7`
- Repetitions: 3; failures: 0

The README/post number must come from the committed benchmark JSON, not from manual text.
