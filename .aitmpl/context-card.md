# Agent Context Card: model-drift-detector

Project: `model-drift-detector` (#22)
Program: `mlops-data-platform`
Claim: One local-first Docker command verifies immutable monitoring batches, detects univariate data and prediction drift with Holm-corrected KS evidence plus a minimum effect, and scores alarm F1 and false positives on deterministic labeled scenarios.
Change: `baseline`

## Read First

1. `AGENTS.md` and `CLAUDE.md`
2. `project.yaml`
3. `.portfolio/component-packs/manifest.yaml`
4. `.portfolio/decision-brain/agent-graph.yaml`
5. `sdd/` and `openspec/changes/baseline/`
6. `openspec/artifacts/`

## Recorded Decisions

- Architecture: pipeline
- API style: cli
- Messaging: none
- Stack and adapters: read `project.yaml`; do not infer from habit.
- Primary benchmark: read `project.yaml`; the number must come from JSON.

## Working Rules

- Keep domain and use cases independent from framework and infrastructure.
- Enforce SRP, OCP, LSP, ISP, and DIP where boundaries exist.
- Use KISS, YAGNI, and DRY without creating speculative abstractions.
- Default to Docker and no paid secret.
- Use Kumo for AWS-like local behavior when cloud behavior is part of the proof.
- Decide explicitly when REST/HTTP, GraphQL, gRPC, a broker, or no broker is justified.
- Before publication, run the benchmark, validation, and reuse-improvement review.

## Agent Handoff

The principal agent coordinates program, architecture, principles, stack, API,
cloud, messaging, language profile, benchmark, design system, security, reuse,
and release roles. If subagents are unavailable, execute those roles in order
and record the same evidence in SDD and OpenSpec artifacts.
