# model-drift-detector Specification

## Purpose

One local-first Docker command verifies immutable monitoring batches, detects univariate data and prediction drift with Holm-corrected KS evidence plus a minimum effect, and scores alarm F1 and false positives on deterministic labeled scenarios.

## Requirements

### Requirement: reproducible portfolio proof

The system SHALL expose a local-first path that proves the primary benchmark
declared in `project.yaml` without paid credentials.

#### Scenario: default verification

- GIVEN the repository is checked out with its committed fixtures
- WHEN the documented Docker or local benchmark command runs
- THEN a JSON result is written under `benchmarks/results/`
- AND the README reports the same measured number

### Requirement: replaceable integrations

The system SHALL keep external providers behind ports or adapters whenever a
provider is not part of the core claim.

#### Scenario: adapter substitution

- GIVEN a local adapter and a future real-provider adapter implement the same port
- WHEN either adapter is selected by configuration
- THEN the application use cases keep the same observable contract
