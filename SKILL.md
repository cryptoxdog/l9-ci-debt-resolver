---
name: ci-debt-resolver
description: reads actual ci failure logs from any repo, classifies tech debt root causes, patches only what logs prove is broken, pushes to remote, and traces prs until ci is green. use when ci is failing due to tech debt, import errors, missing deps, type errors, lint failures, or structural drift and the user wants the agent to fix and converge without assumptions.
skill_schema: 1
layer: control_plane
role: skill_entrypoint
tags: [ci, tech-debt, debugging, pr, convergence, repo-agnostic, l9]
owner: igor_beylin
status: active
version: 1.0.0
updated: 2026-07-02
---

# CI Debt Resolver

## Purpose

Ingest actual CI failure logs. Classify each failure by root cause. Patch only what the logs prove is broken. Push. Poll until green. Leave a traceable artifact trail. No assumptions. No gate weakening.

This skill is repo-agnostic — it reads context from the repo itself and from live CI logs, never from prior knowledge.

## Authority Order

1. Live CI log output (what actually failed, exact traceback)
2. Repo source files (what the code actually does)
3. CI configuration (`.github/workflows/*.yml`, `Makefile`, `pyproject.toml`, `package.json`)
4. This skill's invariants and doctrine
5. Model inference — only for gap-fill, never overrides log evidence

## Core Invariants (non-negotiable)

- **Read logs first.** Never patch before reading `gh run view <id> --log-failed`. If logs are unavailable, classify `unknown/structural` and stop.
- **No gate weakening.** Never skip tests, disable linters, comment out checks, or loosen CI conditions to manufacture green.
- **No assumption patching.** A patch is only valid if its root cause appears verbatim or by traceback in the log. If it doesn't appear in the log, it does not get patched.
- **One commit, one push per cycle.** No `--force-push`. No `--amend` after push.
- **Classify before patch.** Every finding gets a classification record before any file is touched.
- **Fail closed on unknowns.** If a failure cannot be reproduced from log evidence, classify `unknown/structural`. Do not guess.

## Compact Workflow

Each step produces a required gate artifact. Do not advance without it.

```
STEP 1  INGEST       → Gate A: log_parse artifact
STEP 2  CLASSIFY     → Gate B: findings_manifest artifact
STEP 3  PATCH        → Gate C: patch_manifest artifact
STEP 4  LOCAL GATE   → Gate D: local_gate_report artifact
STEP 5  COMMIT+PUSH  → Gate E: push_record artifact
STEP 6  POLL CI      → Gate F: ci_poll_record artifact
STEP 7  THREAD REPLY → Gate G: reply_record artifact
```

Load [references/workflow-protocol.md](references/workflow-protocol.md) for full step definitions and gate artifact schemas.

## Activation Signals

**Strong (activate on any one):**
- "ci is failing / broken / red"
- "fix and push to remote"
- "trace pr for ci error"
- "tech debt causing ci failures"
- "get ci green"

**Reject (do not activate):**
- User asks to disable or skip a failing check without fixing it
- No CI system exists or no `gh` / equivalent CLI is available
- Failure is a runtime production incident, not a CI gate failure
- User explicitly says "don't touch the code"

## Expert Heuristics

```yaml
- condition: "log shows ModuleNotFoundError or ImportError"
  judgment: "PYTHONPATH is not set in the CI job env block, or dep is missing from pyproject.toml runtime deps"
  action: "check env.PYTHONPATH in workflow yaml first; check pyproject.toml [project.dependencies] second; patch the narrower fix"

- condition: "log shows a test collection error but tests pass locally"
  judgment: "CI chassis is missing a module the test imports; local env has it installed globally"
  action: "classify unknown/structural if the module is not in deps; do not add it blindly — verify against pyproject.toml first"

- condition: "a job fails with 'command not found' or step has no 'Install deps'"
  judgment: "the job is missing a dependency install step that other jobs have"
  action: "locate the install step in a sibling job in the same workflow file and mirror it"

- condition: "two PRs touch the same file and one is behind main"
  judgment: "merge conflict risk is high even if CI shows no error yet"
  action: "flag as merge_risk in findings manifest before patching either PR"

- condition: "log shows a type error in a file that was not changed in this PR"
  judgment: "pre-existing type debt was exposed by a new import or stricter CI config"
  action: "classify as pre_existing_debt; patch only if it blocks the current PR's CI gate"
```

## Adapter Map

```yaml
core_default: "repo-agnostic behavior driven entirely by log evidence"

adapters:
  - name: github-actions
    load_when: [".github/workflows/ directory exists", "gh CLI available"]
    changes:
      - log_fetch_command: "gh run view <run_id> --log-failed"
      - pr_check_command: "gh pr checks <N>"
      - poll_command: "gh run list --branch <branch> --limit 3"

  - name: python-uv
    load_when: ["pyproject.toml exists", "uv.lock exists"]
    changes:
      - local_gate_A: "python -m compileall ."
      - local_gate_B: "ruff check ."
      - local_gate_C: "pytest -q"
      - local_gate_D: "uv sync --locked exits 0"
      - dep_add_command: "uv add <package>"

  - name: node-npm
    load_when: ["package.json exists", "no pyproject.toml"]
    changes:
      - local_gate_A: "npx tsc --noEmit"
      - local_gate_B: "npx eslint ."
      - local_gate_C: "npm test"
      - local_gate_D: "npm ci exits 0"
      - dep_add_command: "npm install <package>"
```

## Output Artifacts

Every run appends (never overwrites):

```
reports/CI_DEBT_FINDINGS.jsonl         — one record per finding per cycle
reports/CI_DEBT_CONVERGENCE_REPORT.md  — cycle log per PR/branch
reports/gate_artifacts/<branch>_cycle_<N>/  — gate A-D stdout files
```

Load [references/output-schema.md](references/output-schema.md) for JSONL field definitions.

## Failure Handling

```yaml
- mode: logs_unavailable (HTTP 410 or auth failure)
  prevention: classify unknown/structural; surface to user; do not patch

- mode: patch_breaks_local_gate
  prevention: revert patch; re-classify finding; start next cycle with fresh log

- mode: ci_not_converging_after_max_cycles
  prevention: emit BLOCKED_AT_CAP record; surface all remaining unknowns; stop

- mode: finding_requires_invented_dependency
  prevention: label Unknown; do not add dep without log evidence of its absence

- mode: doctrine_violation_detected_mid_patch
  prevention: halt that branch; post comment explaining violation; continue to next branch
```

## Resource Map

| Reference | Load When |
|---|---|
| [references/workflow-protocol.md](references/workflow-protocol.md) | Every run — defines all 7 steps and gate artifact schemas |
| [references/classification-rules.md](references/classification-rules.md) | Step 2 — root cause taxonomy and classification logic |
| [references/output-schema.md](references/output-schema.md) | Steps 2–7 — JSONL finding record and convergence report schema |
| [references/local-gate-protocol.md](references/local-gate-protocol.md) | Step 4 — adapter-specific local gate commands and pass/fail/unresolved rules |
| [references/pr-treatment-protocol.md](references/pr-treatment-protocol.md) | Step 7 — CodeRabbit reply format and review thread handling |
| [scripts/validate_skill.py](scripts/validate_skill.py) | Pre-packaging — deterministic structural validation |

## Self-Improvement Hook

Capture only when user reports a bad run or requests iteration:

```yaml
after_use_capture:
  - finding_classified_wrong_root_cause
  - patch_introduced_new_failure
  - local_gate_passed_but_ci_failed
  - pr_not_found_or_auth_blocked
```
