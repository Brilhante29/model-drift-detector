# Auditable Drift Requirements

## Artifact Integrity

The system SHALL consume schema version 1 monitoring-batch manifests and SHALL verify path containment, byte count, SHA-256, rows, column order, roles, nullability, and finite numeric values before detection.

### Tampered Payload

Given a payload whose bytes differ from the manifest, detection SHALL fail before parsing and SHALL return nonzero.

## Statistical Evidence

The system SHALL compute two-sided KS evidence per numeric feature and prediction column, SHALL apply Holm family-wise correction, and SHALL require a minimum KS effect before a column is drifted.

### Significance Without Effect

Given adjusted significance with effect below 0.10, the column SHALL not be marked drifted.

## Claim Boundary

The system SHALL describe feature and prediction drift as proxies and SHALL NOT claim model-performance decay without targets.

## Benchmark

The system SHALL score all supported labeled scenarios, preserve confusion counts and per-column evidence, report F1/FPR/p50/p95, and preserve correlation-only limitations separately.

### Publication

Benchmark evidence SHALL remain pending until three successful runs on one immutable Docker image are retained and strict project validation passes.
