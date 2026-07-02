<!-- L9_META
l9_schema: 1
parent: ci-debt-resolver
layer: reference
role: output_schema
tags: [ci, schema, jsonl, output, artifacts]
owner: igor_beylin
status: active
version: 1.0.0
updated: 2026-07-02
/L9_META -->

# Output Schema

## CI_DEBT_FINDINGS.jsonl

One record per finding per cycle. Append only. Never overwrite.

```jsonl
{
  "pr": "<N or branch_name>",
  "cycle": 1,
  "finding_id": "CI-IMPORT-001-cycle1",
  "source": "log | review_comment | static_analysis",
  "severity": "blocking | warning | info",
  "classification": "valid_current | unknown/structural | pre_existing_debt | merge_conflict_risk | doctrine_violation",
  "root_cause_category": "<from taxonomy>",
  "location": "file.py:42",
  "description": "ModuleNotFoundError: No module named 'src' in job 'test' step 'Run tests'",
  "action": "patch | not_patched | surface_to_user",
  "patch_applied": true,
  "commit_sha": "abc1234 | null",
  "ci_conclusion": "success | failure | pending | null"
}
```

---

## CI_DEBT_CONVERGENCE_REPORT.md

Markdown log per branch/PR. Append one cycle block per cycle. Never overwrite.

```markdown
# CI Debt Convergence Report

## Branch: <branch_name> | PR: <N>

### Cycle 1 — <ISO timestamp>

**Findings:** 3 valid_current, 1 unknown/structural, 0 doctrine_violation

**Patches Applied:**
- CI-IMPORT-001: Added `PYTHONPATH: ${{ github.workspace }}` to `ai-review.yml` jobs
- CI-DEPS-001: Added `pydantic>=2.0` to `pyproject.toml` [project.dependencies]

**Local Gates:**
- A (compile): PASS
- B (lint): PASS
- C (tests): UNRESOLVED — chassis module missing (not introduced by patch)
- D (deps): PASS

**Commit:** `abc1234` — fix(ci): CI-IMPORT-001 CI-DEPS-001 — PYTHONPATH + pydantic [cycle 1]
**CI Conclusion:** failure → starting cycle 2

---

### Cycle 2 — <ISO timestamp>

...
```

---

## gate_artifacts/ Directory Structure

```
reports/gate_artifacts/<branch>_cycle_<N>/
  gate_A_compile.txt     — stdout of compile/type check command
  gate_B_lint.txt        — stdout of lint command
  gate_C_tests.txt       — stdout of test command (or UNRESOLVED note)
  gate_D_deps.txt        — stdout of dep install check
```

---

## Final Session Summary (emitted at termination)

```yaml
session_summary:
  status: converged | blocked_at_cap | blocked_logs_unavailable | doctrine_violation_halted
  branches_processed: integer
  branches_converged: integer
  branches_blocked: integer
  total_cycles: integer
  total_findings: integer
  total_patches_applied: integer
  unknowns_surfaced: [string]
  doctrine_violations_surfaced: [string]
  artifacts_written:
    - reports/CI_DEBT_FINDINGS.jsonl
    - reports/CI_DEBT_CONVERGENCE_REPORT.md
    - reports/gate_artifacts/
```
