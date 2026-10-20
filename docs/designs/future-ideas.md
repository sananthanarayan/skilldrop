# Future ideas

Everything raised in the 2026 reviews (the agent-ready-repo comparisons, the OWASP mapping and
the backlog rounds) that hasn't been built. None of it is committed to; [ROADMAP.md](../../ROADMAP.md)
is what's next. Each item says why it matters, roughly how big it is, and what it depends on,
so you can pick one up without re-deriving the context. Sizes are rough: **S** is an hour or
two, **M** a day, **L** several days.

Last reviewed 2026-10-20, after 0.16.34. Organisation governance (AST09) shipped in 0.16.27
([RFC-0050](../rfcs/0050-org-governance.md)), declared containment (AST06) in 0.16.28
([RFC-0051](../rfcs/0051-declared-containment.md)), and the `research`, `comply` and `measure`
loops with a tutorial for each pack added in 0.14.0 in 0.16.29
([RFC-0052](../rfcs/0052-research-comply-measure-loops.md)). The light and heavy tier benchmark
ran in 0.16.21, and every skill now has held-out evals beside its own. 0.16.30 added
`dependency-upgrade-review`, `feedback-synthesis`, `codebase-tour` and `mcp-pairing`, a
compare-packs page, a how-to per skill, and team totals and an HTML dashboard for
`loop-stats`. 0.16.31 added `rollout-plan` and `refactor-plan` after a revision. 0.16.32 checks what a skill's
instructions run against its `permissions` and scans agents ([RFC-0054](../rfcs/0054-instruction-permissions-and-agent-scan.md)). 0.16.33 built the
eval trend and monthly assertion run, OCR for scanned PDFs, joined PDF tables across pages, and
checked the converters' output in Word and Excel. 0.16.34 added `skilldrop search` and ran the CLI
on Windows in CI ([RFC-0056](../rfcs/0056-search-and-windows-ci.md)).

## Distribution

| Idea | Why | Size | Depends on |
|---|---|---|---|
| **`skilldrop install <skill>@<version>`** | Install a specific skill version from the catalogue's history, not just the latest or a commit pin. | M | Version-to-commit lookup, from git tags |
| **IDE auto-detection and `--ide all`** | Install into every tool found in the repo (`.cursor/`, `.kiro/`, `.github/`, `.agents/`) in one command. Listed as design-only in the CLI design doc. | M | — |

## Security (from the OWASP gaps)

| Idea | Why | Size | Depends on |
|---|---|---|---|
| **Signed catalogues** | Commit pins stop a moved tag but don't prove who wrote the commit (AST02). Verify a signature (Sigstore or git commit signing) before install. | L | A key-distribution decision, ideally without adding dependencies |
| **Opt-in semantic scan** | The scan is pattern matching (AST08). An opt-in `scan --deep` could have a model read each skill against the OWASP list. | M | An API key; kept off by default to stay offline |

## Quality and evals

| Idea | Why | Size | Depends on |
|---|---|---|---|
| **Turn on the weekly evals** | The workflow, the monthly assertion run and the trend on the site are all built ([RFC-0055](../rfcs/0055-eval-history-branch.md)); they skip without an `ANTHROPIC_API_KEY` secret. Set `EVALS_MONTHLY_BUDGET` to change the monthly cap from $20. | S | You adding the secret |
| **PDF columns closer than two spaces** | `file-to-markdown` splits PDF table columns on two or more spaces, so a right-aligned number column next to a left-aligned one (Word's "Spend" and "Renewal") merges into one cell. Reading column positions from `pdftotext -bbox` would separate them. | M | — |
