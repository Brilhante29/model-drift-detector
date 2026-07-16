# Change Proposal: baseline

Project: `model-drift-detector` (#22)

## Intent

One local-first Docker command verifies immutable monitoring batches, detects univariate data and prediction drift with Holm-corrected KS evidence plus a minimum effect, and scores alarm F1 and false positives on deterministic labeled scenarios.

## Why This Change Exists

Describe the smallest change that improves the measurable claim or removes a
known portfolio risk.

## Scope

- In scope: <scope>
- Out of scope: paid credentials, unrelated infrastructure, and unmeasured features.

## Portfolio Impact

Program: `mlops-data-platform`

This change should produce evidence, fixtures, decisions, or components that
can be reused by sibling repositories without moving project-specific behavior
into the kit.

## Acceptance Signal

The benchmark in `project.yaml` remains reproducible and its result is recorded
in `benchmarks/results/`.
