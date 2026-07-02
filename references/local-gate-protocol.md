<!-- L9_META
l9_schema: 1
parent: ci-debt-resolver
layer: reference
role: local_gate_protocol
tags: [ci, local-gates, adapters, validation, pre-commit]
owner: igor_beylin
status: active
version: 1.0.0
updated: 2026-07-02
/L9_META -->

# Local Gate Protocol

## Gate Execution Rules

Run all 4 gates in sequence before every commit. Do not skip. Do not reorder.

**Gate A — Compile / Type Check**
**Gate B — Lint**
**Gate C — Tests**
**Gate D — Dependency Install**

Gate status values:
- `PASS` — command exits 0 with no errors
- `FAIL` — command exits non-zero or reports errors; **blocks commit**
- `UNRESOLVED` — command fails due to missing CI chassis module not in project deps; **does not block commit but must be noted in commit message**

---

## Adapter Commands

### Python / uv (load when `pyproject.toml` + `uv.lock` present)

```bash
# Gate A — Compile
python -m compileall .

# Gate B — Lint
ruff check .

# Gate C — Tests
pytest -q
# If collection fails on missing chassis module → UNRESOLVED, not FAIL

# Gate D — Deps
uv sync --locked
```

### Python / pip (load when `requirements.txt` or `setup.py`, no `uv.lock`)

```bash
# Gate A
python -m compileall .

# Gate B
ruff check . || flake8 .

# Gate C
pytest -q

# Gate D
pip install -r requirements.txt --dry-run 2>&1 | grep -i error
```

### Node / TypeScript (load when `package.json`, no `pyproject.toml`)

```bash
# Gate A
npx tsc --noEmit

# Gate B
npx eslint . --max-warnings 0

# Gate C
npm test -- --passWithNoTests

# Gate D
npm ci --dry-run 2>&1 | grep -i error
```

### Make / CI ladder (load when `Makefile` with standard L9 targets)

```bash
# Preferred — runs all gates in canonical order
make format
make lint
make type
make test
# Done when: make ci exits 0
```

---

## UNRESOLVED Classification Rules

Classify Gate C as UNRESOLVED (not FAIL) only when ALL of:
1. Test collection error names a module not in `[project.dependencies]` or `devDependencies`
2. The same module is not imported by any file changed in this patch
3. The error would also appear on `main` branch (pre-existing)

If any condition is false → classify as FAIL → do not commit.

---

## Commit Message Note Format for UNRESOLVED

When committing with one or more UNRESOLVED gates, append to commit message:

```
[UNRESOLVED: Gate C — chassis module '<name>' missing from deps, pre-existing]
```
