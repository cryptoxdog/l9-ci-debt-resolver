---
name: ci-debt-resolver-agents
description: Agents definition for the ci-debt-resolver repository
author: Manus AI
date: 2026-07-02
version: 1.0.0
---

# Agents for CI Debt Resolver

This repository contains the `ci-debt-resolver` skill, which is designed to be executed by autonomous agents.

## Supported Agents
- **Manus AI**: Can natively execute this skill by reading `SKILL.md` and following its workflow protocol.

## Integration
To integrate this skill with an agent, ensure the agent has access to:
- The target repository's source code.
- Live CI logs (e.g., via `gh` CLI).
- The `references/` directory for protocol and schema definitions.
