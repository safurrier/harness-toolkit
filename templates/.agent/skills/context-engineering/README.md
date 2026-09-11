# Context Engineering

This repo vendors a lightweight context-engineering workflow so docs routing and
durable knowledge can evolve with the code.

## Quick Start

- Use `docs/AGENTS.md` as the routing index for agents
- Keep durable explanations in `docs/explanation/`
- Keep stable standards in `docs/reference/`
- Record durable project context in `docs/explanation/` and stable standards in
  `docs/reference/`; keep transient implementation notes out of the generated
  repository contract

## Relationship To The Task Contract

This workflow keeps durable guidance discoverable. It complements `mise run
check` for quality and explicit named routes for heavier product
verification; it does not replace either command.
