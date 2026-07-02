<!-- L9_META
l9_schema: 1
parent: ci-debt-resolver
layer: reference
role: workflow_protocol
tags: [ci, workflow, gates, steps, convergence]
owner: igor_beylin
status: active
version: 1.0.0
updated: 2026-07-02
/L9_META -->

# Workflow Protocol

## Step Definitions and Gate Artifact Schemas

max_cycles_per_branch: 5 (configurable via user instruction)
poll_interval: 90s
poll_timeout: 10min

---

## STEP 1 — INGEST

**Purpose:** Read actual CI failure logs. Do not rely on PR description, commit messages, or prior knowledge.

**Commands (GitHub Actions adapter):**
```bash
gh pr view <N> --json headRefName,headRefOid,title,body
gh pr checks <N>                          # get run IDs for failing checks
gh run view <run_id> --log-failed         # fetch failure log for each failing run
gh pr review <N>                          # ingest inline review comments
```

**Rules:**
- If `gh run view` returns HTTP 410 Gone → log is expired → classify as `unknown/structural`.
- Fetch logs for ALL failing checks, not just the first one.
- Capture the exact error line, file, and line number from each log.

### Gate A Artifact: log_parse

```yaml
log_parse:
  branch: "{branch_name}"
  pr: "{PR number or 'branch'}"
  cycle: "{N}"
  runs_fetched: ["{run_id_1}", "{run_id_2}"]
  failures_found:
    - run_id: string
      job: string
      step: string
      error_line: string
      file: string | Unknown
      line_number: integer | Unknown
  review_comments_found: ["{comment_id}: {location}: {text}"]
  logs_unavailable: ["{run_id}: {reason}"]
```

**STOP if:** All logs are unavailable or expired. Emit blocked status. Do not proceed to Step 2.

---

## STEP 2 — CLASSIFY

**Purpose:** Assign a root cause classification to each failure. No patches until every finding is classified.

Load [classification-rules.md](classification-rules.md) for the full taxonomy.

**Classification values:**
- `valid_current` — log proves this is real and patchable now
- `unknown/structural` — log expired, environment-specific, or cannot be reproduced from evidence
- `pre_existing_debt` — failure existed before this PR; only patch if it blocks current PR gate
- `merge_conflict_risk` — overlapping file changes across open PRs
- `doctrine_violation` — patch would require weakening a gate or breaking an invariant

**Rule:** Only `valid_current` findings get patched in this cycle.

### Gate B Artifact: findings_manifest

```yaml
findings_manifest:
  branch: string
  cycle: integer
  total_findings: integer
  findings:
    - finding_id: string          # e.g. "CI-IMPORT-001-cycle1"
      source: "log | review_comment | static_analysis"
      severity: "blocking | warning | info"
      classification: "valid_current | unknown/structural | pre_existing_debt | merge_conflict_risk | doctrine_violation"
      location: "file:line"
      description: string
      action: "patch | not_patched | surface_to_user"
      root_cause_category: string   # from classification-rules.md taxonomy
  patch_count: integer
  skipped_count: integer
  unknowns_count: integer
```

---

## STEP 3 — PATCH

**Purpose:** Apply minimal diffs for `valid_current` findings only.

**Rules:**
- Apply known root cause fixes first (see [classification-rules.md](classification-rules.md) known patterns section).
- Touch only the lines required to fix the finding. Do not refactor adjacent code.
- If a patch would require adding a new dependency not evidenced by the log, label it `Unknown` and skip.
- If two findings conflict (e.g., same file different fix), resolve the higher-severity finding first.

### Gate C Artifact: patch_manifest

```yaml
patch_manifest:
  branch: string
  cycle: integer
  patches_applied:
    - finding_id: string
      file: string
      change_description: string
      lines_changed: integer
  patches_skipped:
    - finding_id: string
      reason: string
  new_deps_added: ["{package}: {justification}"]
  files_touched: [string]
```

---

## STEP 4 — LOCAL GATE

**Purpose:** Verify the patch does not break anything locally before committing.

Load [local-gate-protocol.md](local-gate-protocol.md) for adapter-specific commands.

**All 4 gates must pass or be UNRESOLVED (not FAIL) before commit:**

| Gate | Check | Fail Behavior |
|------|-------|---------------|
| A | Compile / type check | Do not commit if FAIL |
| B | Lint | Do not commit if FAIL |
| C | Tests | UNRESOLVED allowed if chassis missing; FAIL blocks commit |
| D | Dep install locked | Do not commit if FAIL |

**UNRESOLVED** = structural blocker not introduced by this patch (e.g., missing CI chassis module). Permitted to commit with a note in the commit message.

### Gate D Artifact: local_gate_report

```yaml
local_gate_report:
  branch: string
  cycle: integer
  gate_A: "PASS | FAIL | UNRESOLVED"
  gate_B: "PASS | FAIL | UNRESOLVED"
  gate_C: "PASS | FAIL | UNRESOLVED"
  gate_D: "PASS | FAIL | UNRESOLVED"
  gate_A_output: string
  gate_B_output: string
  gate_C_output: string
  gate_D_output: string
  commit_authorized: true | false
  blocker_if_not_authorized: string | none
```

---

## STEP 5 — COMMIT + PUSH

**Purpose:** Commit and push with a traceable message. One commit per cycle.

**Commit message format:**
```
fix(ci): <finding-ids> — <one-line description> [cycle <N>]
```

**Example:**
```
fix(ci): CI-IMPORT-001 CI-DEPS-001 — add PYTHONPATH env + pydantic dep [cycle 2]
```

**Rules:**
- No `--force-push`.
- No `--amend` after push.
- If `gate_A` or `gate_B` is FAIL, do not commit.

### Gate E Artifact: push_record

```yaml
push_record:
  branch: string
  cycle: integer
  commit_sha: string
  commit_message: string
  push_status: "success | failed"
  push_error: string | none
```

---

## STEP 6 — POLL CI

**Purpose:** Wait for CI to complete on the pushed commit. Do not assume green.

**Commands:**
```bash
gh run list --branch <branch> --limit 3
gh run view <run_id>   # repeat every 90s until conclusion in {success, failure, cancelled}
```

**Timeout:** 10 minutes. If timeout reached, record `conclusion: timeout` and start next cycle.

**On failure:** Go to Step 1 of next cycle with fresh log ingest. Do not reuse prior log parse.

**On success:** Record convergence. Do not open next cycle.

### Gate F Artifact: ci_poll_record

```yaml
ci_poll_record:
  branch: string
  cycle: integer
  run_id: string
  head_sha: string
  conclusion: "success | failure | cancelled | timeout"
  poll_duration_seconds: integer
  converged: true | false
```

---

## STEP 7 — THREAD REPLY

**Purpose:** Reply to every CodeRabbit or reviewer inline comment addressed by this cycle's commit.

**Reply format:**
```
Implemented in <commit-SHA>. Fix: <one sentence>.
Local gates: A=<result> B=<result> C=<result> D=<result>.
CI: <conclusion or 'pending'>.
```

**Rules:**
- Reply only to comments addressed by this cycle's patches.
- Do not reply to comments for skipped or unknown findings without first noting the skip reason.

### Gate G Artifact: reply_record

```yaml
reply_record:
  branch: string
  cycle: integer
  replies_posted:
    - comment_id: string
      commit_sha: string
      reply_text: string
  replies_skipped:
    - comment_id: string
      reason: string
```

---

## Termination Conditions

Session ends when one of:

- **(a) Converged** — All target branches/PRs show `ci_poll_record.conclusion = success` on their head SHA.
- **(b) Capped** — `max_cycles_per_branch` reached on all remaining branches. Emit `BLOCKED_AT_CAP` record. Surface remaining unknowns.
- **(c) Doctrine violation** — A violation is detected mid-patch. Halt that branch. Post comment. Continue to next branch.
- **(d) All logs unavailable** — All run logs are expired or auth-blocked. Emit blocked status. Surface to user.
