# Change Design: baseline

## Decision

- Architecture: pipeline
- Stack: python-3.12
- API style: cli
- Messaging: none
- Cloud mode: local-first; real providers stay behind adapters.

## Boundaries

- Domain and use cases define behavior.
- Infrastructure implements ports.
- Interfaces expose the contract and benchmark command.

## Engineering Rules

- Decouple policy from mechanism.
- Apply SRP, OCP, LSP, ISP, and DIP at the boundaries that matter.
- Prefer KISS and YAGNI over speculative abstractions.
- Keep replacement adapters behaviorally compatible with the same port (LSP).
- Test use cases without HTTP, cloud SDKs, brokers, or UI.

## Rejected Alternatives

Record the architecture, library, transport, broker, or cloud alternatives
that were considered and why they do not improve this claim.
