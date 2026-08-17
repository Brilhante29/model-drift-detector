---
name: local-first-ai-evidence
description: Build or review local-first LLM, RAG, prompt, agent, embedding, or inference benchmarks with pinned providers, provenance-bound artifacts, and offline evaluation.
---

# Local-first AI Evidence

1. Separate provider execution from evaluation through a versioned file contract; hide expected answers from generation.
2. Keep HTTP/Ollama/FastEmbed adapters outside metric, ranking, and tool policy.
3. Pin model digest or immutable revision and fail on drift, empty output, missing usage, or provider errors.
4. Record producer commit/image, model identity, artifact hashes, workload, failures, tokens, latency, and cost scope.
5. Pin cross-repository producers by exact SHA and regenerate their artifact in consumer CI.
6. Preserve ties and failures; do not manufacture fallback success.
7. Generate on an explicit local network, evaluate committed artifacts offline, and publish V2 from a clean commit and exact image.
