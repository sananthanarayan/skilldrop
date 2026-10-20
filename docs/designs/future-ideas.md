# Future ideas

Everything raised in the 2026 reviews (the agent-ready-repo comparisons, the OWASP mapping and
the backlog rounds) that hasn't been built. None of it is committed to; [ROADMAP.md](../../ROADMAP.md)
is what's next. Each item says why it matters, roughly how big it is, and what it depends on,
so you can pick one up without re-deriving the context. Sizes are rough: **S** is an hour or
two, **M** a day, **L** several days.

Last reviewed 2026-10-20, after 0.16.31. Organisation governance (AST09) shipped in 0.16.27
([RFC-0050](../rfcs/0050-org-governance.md)), declared containment (AST06) in 0.16.28
([RFC-0051](../rfcs/0051-declared-containment.md)), and the `research`, `comply` and `measure`
loops with a tutorial for each pack added in 0.14.0 in 0.16.29
([RFC-0052](../rfcs/0052-research-comply-measure-loops.md)). The light and heavy tier benchmark
ran in 0.16.21, and every skill now has held-out evals beside its own. 0.16.30 added
`dependency-upgrade-review`, `feedback-synthesis`, `codebase-tour` and `mcp-pairing`, a
compare-packs page, a how-to per skill, and team totals and an HTML dashboard for
`loop-stats`. 0.16.31 added `rollout-plan` and `refactor-plan` after a revision.

## Distribution

| Idea | Why | Size | Depends on |
|---|---|---|---|
| **`skilldrop install <skill>@<version>`** | Install a specific skill version from the catalogue's history, not just the latest or a commit pin. | M | Version-to-commit lookup, from git tags |
| **IDE auto-detection and `--ide all`** | Install into every tool found in the repo (`.cursor/`, `.kiro/`, `.github/`, `.agents/`) in one command. Listed as design-only in the CLI design doc. | M | — |
| **`skilldrop search <words>`** | Search descriptions from the terminal. The site has search; the CLI doesn't. Also design-only. | S | — |
| **Windows CI** | The CLI has never run in CI on Windows. Paths, `git` calls and file permissions are the likely breaks. | M | — |

## Security (from the OWASP gaps)

| Idea | Why | Size | Depends on |
|---|---|---|---|
| **Signed catalogues** | Commit pins stop a moved tag but don't prove who wrote the commit (AST02). Verify a signature (Sigstore or git commit signing) before install. | L | A key-distribution decision, ideally without adding dependencies |
| **Permissions for instruction-only skills** | A skill with no scripts can still tell the agent to run commands or fetch URLs, and today it declares nothing. Extend `permissions` to the instructions themselves. | M | Design: how to check prose against a declaration |
| **Opt-in semantic scan** | The scan is pattern matching (AST08). An opt-in `scan --deep` could have a model read each skill against the OWASP list. | M | An API key; kept off by default to stay offline |
| **Scan agents, not just skills** | `skilldrop scan` covers skills; subagent files aren't scanned. | S | — |

## Quality and evals

| Idea | Why | Size | Depends on |
|---|---|---|---|
| **Turn on the weekly evals** | The workflow exists but skips without an `ANTHROPIC_API_KEY` secret. | S | You adding the secret |
| **Eval trend on the site** | Publish each weekly run's results to the *How skills are checked* page, so trigger accuracy is visible over time. | M | Weekly evals running |
| **Monthly assertion evals** | Run the acceptance assertions on a schedule, not only by hand. They cost more than trigger checks. | S | Weekly evals running; a budget |
| **Open the converters' output in real Word and Excel** | The .docx and .xlsx files are checked in Quick Look only. | S | Someone with Office |
| **OCR for scanned PDFs** | `file-to-markdown` stops at a PDF with no text layer. Tesseract could add a text layer first. | M | An optional system dependency |
| **Tables split across PDF pages** | A table that starts at the foot of one page loses its header row to that page. | S | — |
