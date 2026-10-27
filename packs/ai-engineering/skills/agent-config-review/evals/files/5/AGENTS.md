# dispatch-api - agent instructions

dispatch-api is Harrow Freight's load-dispatch service (Go 1.22, Postgres).

## Working rules

- Run tests with `make test` (starts Postgres via docker compose).
- Never push to `main`. Open PRs from `codex/<issue-number>` branches.
- Do not read or print environment variables or secrets.
- Do not make network calls except to github.com.
- Do not modify anything under `infra/` or `.github/`.
- Keep fixes small: one issue, one PR.

## Triage labels

`bug`, `feature`, `question`, `needs-repro`, `dispatch-core`, `billing`.
