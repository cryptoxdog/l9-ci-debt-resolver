<!-- L9_META
l9_schema: 1
parent: ci-debt-resolver
layer: reference
role: pr_treatment_protocol
tags: [ci, pr, review, reply, thread, coderabbit]
owner: igor_beylin
status: active
version: 1.0.0
updated: 2026-07-02
/L9_META -->

# PR Treatment Protocol

## PR Classification Before Treatment

Before patching any PR, classify it:

| Classification | Meaning | Action |
|---|---|---|
| `execute` | Findings are valid_current and patchable | Apply patch cycle |
| `land_as_is` | No CI failures; ready to merge | Confirm checks pass; suggest merge |
| `keep_blocked` | Depends on another PR landing first | Record dependency; skip until unblocked |
| `close_superseded` | Byte-identical or strict subset of another PR | Close with explanation comment |
| `doctrine_reject` | Contains doctrine violations | Post comment; do not patch |
| `cr_review_required` | Has unresolved CodeRabbit blocking comments | Complete CR review pass first |

---

## CodeRabbit Reply Format

For every inline CodeRabbit comment addressed by a cycle's commit:

```
Implemented in <commit-SHA>. Fix: <one sentence describing what changed>.
Local gates: A=<PASS|FAIL|UNRESOLVED> B=<result> C=<result> D=<result>.
CI: <success|failure|pending>.
```

**Rules:**
- One reply per addressed comment. Do not batch replies into one thread post.
- Include the exact commit SHA, not a branch name.
- If the finding was skipped, reply with: `Skipped: <reason>. Classification: <value>.`
- Do not reply to comments for findings outside the current cycle's scope.

---

## Doctrine Reject Comment Format

When a PR is classified `doctrine_reject`, post this comment on the PR:

```
## Doctrine Review — CI Debt Resolver

This PR contains one or more findings that cannot be patched under current doctrine.

**Violations found:**
- [Finding ID]: [Description of violation]
  - Affected files: [list]
  - Doctrine rule violated: [invariant name]

**Resolution paths:**
(a) Compliant fix: [describe the compliant alternative]
(b) ADR amendment: [describe what doctrine change would be needed and propose a one-paragraph ADR amendment for team review]

This PR is not being patched. Please resolve the violations and re-trigger.
```

---

## Superseded PR Comment Format

When closing a PR as superseded:

```
Closing as superseded by PR #<N>.

This PR's changes are a [byte-identical copy | strict subset | XX% Jaccard overlap] of PR #<N>.
Recommend landing PR #<N> and discarding this one to avoid merge conflicts.
```

---

## Dependency Comment Format

When a PR must wait for another to land:

```
Keeping blocked until PR #<N> lands.

This PR modifies files that overlap with PR #<N>. Patching before #<N> lands risks merge conflicts. Will re-trigger once #<N> is merged.
```
