# #22 model-drift-detector: drift_alarm_f1 = 1.0

One local-first Docker command verifies immutable monitoring batches, detects univariate data and prediction drift with Holm-corrected KS evidence plus a minimum effect, and scores alarm F1 and false positives on deterministic labeled scenarios.

This repository belongs to the MLOps and Data Platform program. Its job is narrow: prove the measurable claim through the selected component pack before adding unrelated infrastructure or features.

The benchmark is the proof: alarm F1 1.0, false-positive rate 0.0, and median p95 35.48 ms across three source-locked Docker runs. The corrected non-root default command and Benchmark Result V2 evidence agree.

The important architecture decision is pipeline. The dominant force is an ordered evidence flow: verify artifacts, parse batches, compute statistics, correct hypotheses, apply alarm policy, emit telemetry, and score decisions.

The default path stays local-first. The project uses python-ml, exposes cli, uses messaging mode `none`, and stores data with `none`. The dependency rule is explicit: Artifact, SciPy, telemetry, and CLI adapters depend on domain values and application protocols; the domain never depends on an external framework.

The rejected work matters as much as the implemented work. Anything that does not improve the benchmark stays out of the first version.

Post angle: start with the number, show the architecture boundary, then explain which future adapter can be added without changing the core use cases.
