# Proposal: ship model-drift-detector

## Why

The MLOps portfolio can train, promote, and serve a model but lacks a strict post-deployment monitoring boundary. A monitor must prove alarm behavior, not only render distribution charts.

## What Changes

- Add an immutable monitoring-batch consumer with SHA-256-before-parse.
- Add a replaceable SciPy KS detector and framework-independent alarm policy.
- Add Holm multiple-test control and a minimum effect.
- Add bounded Prometheus metrics and file-oriented CLI.
- Add deterministic labeled scenario evaluation with F1, false positives, runtime, and a known blind spot.
- Patch reusable contract, skill, docs, component pack, installer, schema, and validators into the kit.

## Impact

#22 becomes the monitoring stage after #21 and establishes shared boundaries for #23 and #26 without source-code coupling.
