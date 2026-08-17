---
name: local-first-ai-evidence
description: Build or review local-first LLM, RAG, prompt, agent, embedding, or inference benchmarks that use pinned model/provider adapters, provenance-bound artifacts, and provider-neutral offline evaluation. Use when AI outputs must be real, reproducible, Dockerized, and replaceable by cloud providers without coupling the metric core.
---

# Local-first AI Evidence

1. Separate model execution from evaluation with a versioned file contract. Keep expected answers out of model-visible inputs.
2. Put OpenAI-compatible HTTP, Ollama, FastEmbed, or another provider in an outer adapter. Keep metrics, ranking, tools, and policy independent of the provider.
3. Pin model name plus immutable digest/revision. Fail closed on empty responses, missing usage, artifact drift, or a moved model revision.
4. Record producer source commit, Docker image digest, model digest/revision, input/output hashes, measured count, failures, tokens, latency, and cost scope.
5. For cross-repository inputs, commit `contracts/producers.lock.json`, checkout the exact producer SHA in CI, generate a fresh artifact, then evaluate it.
6. Preserve negative results, ties, planner failures, and tool failures. Never replace observed failures with fallback success.
7. Run generation on an explicit local network; run committed-artifact evaluation with `--network none`.
8. Publish V2 evidence from a clean source commit and exact image, then require CI success on the final `main` SHA.

Use `contracts/prediction-artifact.schema.json` for RAG/answer outputs and `contracts/producer-lock.schema.json` for pinned inter-repository edges.
