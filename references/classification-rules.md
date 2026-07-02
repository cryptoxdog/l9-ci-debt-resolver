<!-- L9_META
l9_schema: 1
parent: ci-debt-resolver
layer: reference
role: classification_rules
tags: [ci, classification, root-cause, taxonomy, tech-debt]
owner: igor_beylin
status: active
version: 1.0.0
updated: 2026-07-02
/L9_META -->

# Classification Rules

## Root Cause Taxonomy

Use this taxonomy to assign `root_cause_category` in the findings manifest.

| Category | Description | Log Signal |
|---|---|---|
| `env-missing` | CI job env block missing required env var (e.g., PYTHONPATH) | `ModuleNotFoundError`, `ImportError` with no sys.path evidence |
| `dep-missing-runtime` | Package absent from runtime deps in pyproject.toml / package.json | `ModuleNotFoundError: No module named '<pkg>'` |
| `dep-missing-ci-job` | CI job missing install step that sibling jobs have | `command not found`, `module not found` in specific job only |
| `api-drift` | Source file missing field, method, or class that another file imports | `ImportError: cannot import name`, `AttributeError` |
| `type-error` | Strict type checker reports error on real type mismatch | `pyright: error`, `tsc: error TS` |
| `lint-error` | Ruff, eslint, or equivalent reports rule violation | `ruff: E`, `eslint: error` |
| `test-failure` | Test asserts wrong value or behavior | `AssertionError`, `Expected ... Received` |
| `workflow-syntax` | YAML syntax error in CI workflow file | `yaml.scanner.ScannerError`, workflow parsing error |
| `merge-conflict-risk` | Two open PRs touch the same file; not yet a CI failure | Static analysis of open PR file lists |
| `pre-existing-debt` | Failure existed on main before this PR | Same error appears in main branch CI history |
| `unknown/structural` | Log unavailable, expired, or requires CI chassis to reproduce | HTTP 410, auth failure, chassis-only import |
| `doctrine-violation` | Fixing this would require weakening a gate or breaking an invariant | Any patch that requires disabling a check |

---

## Classification Decision Rules

```yaml
classify_as_valid_current_when:
  - exact_error_line_appears_in_fetched_log
  - root_cause_category_is_in_patchable_set: [env-missing, dep-missing-runtime, dep-missing-ci-job, api-drift, workflow-syntax]
  - patch_does_not_require_weakening_any_gate
  - patch_does_not_require_inventing_a_dependency

classify_as_unknown_structural_when:
  - log_is_unavailable_or_expired
  - error_requires_ci_chassis_module_not_in_deps
  - error_cannot_be_reproduced_from_available_evidence

classify_as_pre_existing_debt_when:
  - same_error_exists_in_main_branch_before_this_pr
  - patch_only_if_it_directly_blocks_current_pr_gate

classify_as_doctrine_violation_when:
  - fix_requires_disabling_a_linter
  - fix_requires_commenting_out_a_test
  - fix_requires_loosening_type_strictness_without_adrs
  - fix_requires_adding_noqa_or_type_ignore_without_justification
```

---

## Known Recurring Patterns

These patterns appear repeatedly across Python/TypeScript CI repos. Apply as cycle-1 pre-check before full log analysis. Only apply if the log confirms the pattern — do not apply blindly.

### P-001: PYTHONPATH missing in CI job

**Log signal:** `ModuleNotFoundError: No module named 'src'` or `ModuleNotFoundError: No module named '<repo_root_pkg>'`

**Fix:** Add to each failing job in the workflow YAML:
```yaml
env:
  PYTHONPATH: ${{ github.workspace }}
```

**Do not apply if:** The error names a third-party package (→ P-002 instead).

---

### P-002: Runtime dependency missing from pyproject.toml

**Log signal:** `ModuleNotFoundError: No module named '<package>'` where `<package>` is a third-party lib.

**Fix:** Add to `[project.dependencies]` in `pyproject.toml`:
```toml
[project.dependencies]
<package>>=<min_version>
```

**Do not apply if:** Package is already present; the error is a PYTHONPATH issue (→ P-001).

---

### P-003: CI job missing install step

**Log signal:** A specific job fails with a ModuleNotFoundError that other jobs do not show, and that job has no `pip install` / `uv sync` / `npm ci` step.

**Fix:** Copy the install step from a sibling job in the same workflow file and add it to the failing job. Match the exact command used by sibling jobs.

---

### P-004: Source file missing exported symbol

**Log signal:** `ImportError: cannot import name '<Symbol>' from '<module>'`

**Fix:** Add the missing class, function, field, or dataclass to the source file named in the import. Pattern the implementation on the import's usage context.

---

### P-005: Workflow YAML syntax error

**Log signal:** GitHub Actions workflow parse error before any job runs.

**Fix:** Run `python -c "import yaml; yaml.safe_load(open('.github/workflows/<file>.yml'))"` locally. Fix the offending line. Validate all workflow files before committing.

---

## Doctrine Violation Response

When a finding is classified `doctrine_violation`:

1. Do **not** patch it.
2. Post a comment on the PR/issue explaining:
   - What the violation is.
   - Why the proposed fix violates the invariant.
   - Two resolution paths: (a) a compliant fix, (b) an ADR amendment proposal if doctrine change is warranted.
3. Continue to next branch/PR.
4. Record in `CI_DEBT_FINDINGS.jsonl` with `action: surface_to_user`.
