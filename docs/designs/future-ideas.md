# Future ideas

Everything raised in the 2026 reviews (the agent-ready-repo comparisons, the OWASP mapping and
the backlog rounds) that hasn't been built. None of it is committed to; [ROADMAP.md](../../ROADMAP.md)
is what's next. Each item says why it matters, roughly how big it is, and what it depends on,
so you can pick one up without re-deriving the context. Sizes are rough: **S** is an hour or
two, **M** a day, **L** several days.

Last reviewed 2026-10-01, after 0.16.0.

## Distribution

| Idea | Why | Size | Depends on |
|---|---|---|---|
| **PyPI release** | `pipx install skilldrop-cli` for Python-first teams. The wheel builder exists and was tested locally. | S | A PyPI account and project |
| **Publish to PyPI from CI** | Publish to PyPI with each npm release, via PyPI trusted publishing (OIDC, no stored token). | M | The item above |
| **`skilldrop install <skill>@<version>`** | Install a specific skill version from the catalogue's history, not just the latest or a commit pin. | M | Version-to-commit lookup, from git tags |
| **IDE auto-detection and `--ide all`** | Install into every tool found in the repo (`.cursor/`, `.kiro/`, `.github/`, `.agents/`) in one command. Listed as design-only in the CLI design doc. | M | — |
| **`skilldrop search <words>`** | Search descriptions from the terminal. The site has search; the CLI doesn't. Also design-only. | S | — |
| **Windows CI** | The CLI has never run in CI on Windows. Paths, `git` calls and file permissions are the likely breaks. | M | — |

## Security (from the OWASP gaps)

| Idea | Why | Size | Depends on |
|---|---|---|---|
| **Signed catalogues** | Commit pins stop a moved tag but don't prove who wrote the commit (AST02). Verify a signature (Sigstore or git commit signing) before install. | L | A key-distribution decision, ideally without adding dependencies |
| **Declared containment** | Skills run with the agent host's full permissions (AST06). A `permissions.containment` field could say what sandbox a skill expects, for hosts that can provide one. | M | Agent hosts that expose sandbox settings |
| **Permissions for instruction-only skills** | A skill with no scripts can still tell the agent to run commands or fetch URLs, and today it declares nothing. Extend `permissions` to the instructions themselves. | M | Design: how to check prose against a declaration |
| **Opt-in semantic scan** | The scan is pattern matching (AST08). An opt-in `scan --deep` could have a model read each skill against the OWASP list. | M | An API key; kept off by default to stay offline |
| **Organisation governance** | Inventory, approval and audit are per machine (AST09). An org-level inventory could be built from ledgers, or from the `package` mirrors with `MIRROR.json`. | L | — |
| **Scan agents, not just skills** | `skilldrop scan` covers skills; subagent files aren't scanned. | S | — |

## Quality and evals

| Idea | Why | Size | Depends on |
|---|---|---|---|
| **Turn on the weekly evals** | The workflow exists but skips without an `ANTHROPIC_API_KEY` secret. | S | You adding the secret |
| **Eval trend on the site** | Publish each weekly run's results to the *How skills are checked* page, so trigger accuracy is visible over time. | M | Weekly evals running |
| **Benchmark on the light and heavy tiers** | `run_bench.py` (RFC-0040) has run on the standard tier only. Running all three shows where a cheaper model is enough, per skill. | S | Claude Code usage to spare |
| **Three or more evals per skill** | 69 of 93 skills have one acceptance eval, so a per-skill benchmark number is an anecdote. | L | Authoring time |
| **Monthly assertion evals** | Run the acceptance assertions on a schedule, not only by hand. They cost more than trigger checks. | S | Weekly evals running; a budget |
| **Open the converters' output in real Word and Excel** | The .docx and .xlsx files are checked in Quick Look only. | S | Someone with Office |
| **OCR for scanned PDFs** | `file-to-markdown` stops at a PDF with no text layer. Tesseract could add a text layer first. | M | An optional system dependency |
| **Tables split across PDF pages** | A table that starts at the foot of one page loses its header row to that page. | S | — |

## New skills and loops

| Idea | Why | Size |
|---|---|---|
| **`dependency-upgrade-review`** | A merge verdict on a Dependabot or Renovate PR: what changed, whether the pinned commit matches the release tag, whether CI exercised it, how to roll back. Done by hand for PR #24. | M |
| **`rollout-plan` / `rollback-plan`** | Feature-flag and canary stages with the metrics that decide each step, and how to undo a release, including data and schemas. Partly covered by `migration-plan` and `launch-readiness`. | M |
| **`feedback-synthesis`** | Turn interviews, support tickets or NPS comments into themes with evidence: a gap in the `discover` loop. | M |
| **`codebase-tour`** | Onboard someone to an unfamiliar repo before they implement anything: a gap in the `build` loop. | M |
| **`refactor-plan` / `tech-debt-register`** | Work that is neither a feature nor a bug. | M |
| **`mcp-pairing`** | Recommend which MCP servers suit a loop. The [MCP guide](../../guides/how-to/use-with-mcp-servers.md) covers this as docs; a skill would tailor it. | S |
| **A `research` loop** | plan → synthesise → compare hypotheses, with a gate on evidence strength. All three skills exist. | S |
| **A `comply` loop for GRC** | risk register → DPIA → evidence map → a sign-off gate. | S |
| **A `measure` loop for data** | metric definition → SQL review → dashboard spec. | S |
| **Hand-written tutorials for the new packs** | The eight packs added in 0.14.0 have generated how-to and reference pages but no end-to-end tutorial like the original five packs. | M each |

## Docs and site

| Idea | Why | Size |
|---|---|---|
| **More docs depth** | agent-ready-repo has about 270 doc pages; skilldrop has about 60. Per-skill how-tos are the obvious next layer. | L |
| **Compare packs** | A page that sets two packs side by side for someone choosing between them. | S |
| **Loop run-log dashboard** | A local HTML view of `skilldrop loop-stats --json`, for a team retrospective. | M |
| **Team aggregation of loop stats** | Combine several people's `loop-stats --json` files into one view, still without sending anything anywhere. | S |
