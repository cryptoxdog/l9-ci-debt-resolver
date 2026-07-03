# Regression Guard

- Do not weaken CI gates.
- Export only observed or repaired findings.
- Missing data must be `Unknown`, not invented.
- Dispatch must include source repo, source SHA, run ID, run attempt, and artifact name.
- Validate before dispatch.
- Dispatch token absence must not break corpus export.
- Resolver must not patch downstream repos.
