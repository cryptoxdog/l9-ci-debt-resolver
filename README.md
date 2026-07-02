---
name: ci-debt-resolver-readme
description: README for the ci-debt-resolver repository
author: Manus AI
date: 2026-07-02
version: 1.0.0
---

# CI Debt Resolver

## Overview
CI Debt Resolver is an autonomous agent skill designed to ingest actual CI failure logs, classify tech debt root causes, patch only what the logs prove is broken, push to remote, and trace PRs until CI is green. It operates with strict invariants: no assumptions, no gate weakening, and complete reliance on log evidence.

## Core Features
- **Log-Driven:** Reads `gh run view <id> --log-failed` before any action.
- **Strict Invariants:** Never skips tests, disables linters, or comments out checks.
- **Traceable:** Leaves a clear artifact trail for every classification and patch.
- **Repo-Agnostic:** Reads context from the repo itself and live CI logs, never from prior knowledge.

## Structure
- `SKILL.md`: Main entrypoint and skill definition.
- `references/`: Contains protocol definitions, schemas, and rules.
- `scripts/`: Contains validation scripts for the skill.

## Usage
Activate the skill with signals like:
- "ci is failing / broken / red"
- "fix and push to remote"
- "trace pr for ci error"

For detailed instructions, refer to `SKILL.md`.
