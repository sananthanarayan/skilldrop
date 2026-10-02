# Changelog

What shipped in each released version of `skilldrop-cli`. The site reads the newest three
entries into its **Recently shipped** section (RFC-0026), and `build_site.py` refuses to
build if the version at the top of this file disagrees with `package.json` — so a release
cannot ship undocumented.

Format: `## <version> — <YYYY-MM-DD>`, newest first, one bullet per user-visible change.
Bullets say what a user can now do, not which files moved.

## 0.16.4 — 2026-10-02

- **New skill: `pr-description-writer`** (`dev-team`). Writes a pull request title and description from the diff: why, what changed, the checks that were really run, where a reviewer should look first, and risk and rollback. It also reports what the diff contains that the commits don't mention, such as a dependency bump, a deleted test or a migration.
- **New skill: `tech-debt-register`** (`dev-team`). Turns notes, TODOs and incident write-ups into a ranked register: where each item lives, what it costs today with the evidence, the fix size, a decision and the trigger that reopens it. A cost nobody measured is marked as reported, never estimated.
- **New skill: `security-questionnaire-response`** (`grc`). Drafts answers to a customer's security questionnaire from your own policies and reports, in the customer's form, with the document behind each answer. Questions the evidence doesn't cover are marked as needing input, and conflicts and stale evidence are flagged for the security owner.
- **These three were admitted on a benchmark result** (RFC-0041): three evals each, two trials, two blind judges. Both judges preferred their results to plain Claude Code in 15 and 16 of 18 pairs after one revision. The RFC records the first round too, where they did not clearly win.
- **Install from PyPI as well as npm:** `pipx install skilldrop-cli`, then `skilldrop install --pack <name>`. It still needs Node 16.7 or newer.

## 0.16.3 — 2026-10-02

- **The package, the plugin and the site now say what sets skilldrop apart:** portable skills, measured against the agent without them. The numbers behind that are on the [How skills are checked](https://sananthanarayan.github.io/skilldrop/evals/) page.
- **`run_bench.py --second-judge MODEL`** runs the blind comparison with a second model and reports how often the two judges agree. The published run now includes it.

## 0.16.2 — 2026-10-02

- **29 skills stop showing their machinery.** Replies and artifacts no longer mention the skill, its files, caps or internal terms, or that a run is non-interactive, and they name another skill once, at the end, as a next step. This came from the first benchmark run, where a blind judge marked those replies down.
- **A `BLOCKED` reply now tells you something.** In 13 skills the `BLOCKED: need <X>` line is followed by what is missing in plain words, what you'll get once it's supplied, and anything the request already allows.
- **`adr-generator` records a decision you've already made as `Accepted`.** "We decided" used to produce `Proposed`. Deciders, dates and drivers you didn't give are left out or marked, not guessed.
- **`delivery-metrics-report` no longer stops an unattended run on timestamps with no time zone.** It assumes UTC, says so at the top with the number of rows affected, and says what moves if that's wrong.
- **`strategy-analysis` gives you the framework you asked for.** When another one fits the question better it still says so and runs that one, and now adds yours after it.
- **`agents-md-generator` writes a missing command as a plain "none defined" line** in the file. The `[missing]` marker stays in the provenance table only.
- **Every skill is now measured against plain Claude Code**, with the results on the [How skills are checked](https://sananthanarayan.github.io/skilldrop/evals/) page. 22 evals gained the input files their prompts name, under `evals/files/`.

## 0.16.1 — 2026-10-01

- **`md-to-xlsx` no longer writes a workbook Excel can't open** when a cell holds a number too big to store, such as `1e999`. It is kept as text. A JSON integer longer than 15 digits is kept as text too, so an ID isn't rounded.
- **`md-to-xlsx` tells you when it removes an HTML tag from a table cell.** A name like `Fabrikam <Ltd>` used to lose `<Ltd>` without a word.
- **`file-to-markdown` keeps code blocks and quotes from a Word file.** Code comes back fenced with its indentation, quotes come back with `>`, and literal `<tag>` text is escaped so it survives being converted again.
- **`md-to-docx` says each warning once.** A 60,000-row table with the same problem in every row printed 60,000 lines.
- **`pre-merge-review --install-hook` respects your umask.** The pre-commit hook was always made world-readable (CodeQL `py/overly-permissive-file`); it now gets the execute bit only where the file was already readable.
- The three converter scripts run without deprecation warnings on Python 3.14.

## 0.16.0 — 2026-10-01

- **Pin a third-party catalogue to an exact commit:** `--from <url>#<commit-sha>`. A tag or branch can be moved to different code after you reviewed it, but a commit can't, and the CLI checks it got the commit you asked for. Every install records its commit in the ledger. An unpinned install prints the `#<commit>` URL that gets exactly those files again. Pinned skills stay put on `update` until you re-pin.
- **`outdated` and `update` catch a skill that changed upstream under the same version**, which the version check alone missed. `update` names it and leaves it alone; read it with `skilldrop diff`, then take it with `update --changed`.
- **Skills that ship scripts now declare what those scripts do** (`permissions` in `manifest.json`): the hosts they contact, the programs they run, and where they write. `skilldrop scan` raises any script that does something its skill doesn't declare as a top-severity finding, and `skilldrop validate` fails the catalogue. `skilldrop info` and third-party installs show the declaration. All 24 bundled script skills declare theirs.
- **The scan's network rule catches more:** every `requests` call form, `urlopen`, `http.client` and `aiohttp`. It had missed `figma-diagrams`'s calls to the Figma API.
- **New guide: [Use skills with MCP servers](guides/how-to/use-with-mcp-servers.md).** Which servers (GitHub, Atlassian, Linear, Figma, Sentry, Supabase, AWS cost, Slack) pair with which skills, how to add one in Claude Code, Cursor, Codex, VS Code, Kiro and Antigravity, and how to do it safely. Every endpoint and config key was checked against the vendor's docs.
- The OWASP mapping is updated: update drift (AST07) is now covered, and supply chain (AST02), over-privileged skills (AST03) and cross-platform reuse (AST10) are stronger. Ideas not yet built are collected in [docs/designs/future-ideas.md](docs/designs/future-ideas.md).
- The Claude plugin marketplace now has a description, so `claude plugin validate` passes without a warning.

## 0.15.1 — 2026-10-01

- `file-to-markdown` gets far more out of a PDF. Tables with aligned columns come through as Markdown tables, indented lists stay lists, code stays code, and short standalone lines become headings (it says those were guessed). A table whose cells wrap is kept as aligned text. A page with two columns of prose side by side is read in column order, and the script names those pages. Before, every PDF came out as run-together paragraphs.
- `mermaid-render` shows Mermaid's own parse error ("Parse error on line 6 …") when mermaid-cli can't draw a diagram, not a browser stack trace. Its lint agreed with real Mermaid (mermaid-cli 12.0.0) on all 57 diagrams tested: every one in the repo plus 21 edge cases.
- The `terraform-module` example now passes `terraform fmt -check` and `terraform validate` (Terraform 1.16.4), with the AWS provider at 5.0.0, 5.100.0 and 6.67.0. That's both ends of the range it declares. `terraform-plan-review`'s script was checked against real plans from Terraform 1.16.4, and flags an IAM wildcard, a public bucket policy and open SSH, without ever printing a secret from the plan.

## 0.15.0 — 2026-10-01

- Every pack has a how-to and a reference page in the docs: install it, run its first task, follow a typical session and its loops; then every skill's output, needs, quality bar, hand-offs and what it isn't for. They're generated from the skills' own files, so they stay current. Find them under *Per pack* in the docs.
- `skilldrop package <dir> --pack dev-team,design` copies a vetted subset of the catalogue into a standalone one you can host on an internal git server. `MIRROR.json` records where every file came from and its SHA-256.
- `skilldrop init-catalogue <dir>` starts a private catalogue for your team's own skills, with an example skill and a workflow that validates and scans every pull request.
- Loops can keep a local log of their gate verdicts. Set `SKILLDROP_LOOP_LOG` to a file path, and `skilldrop loop-stats` shows which gates pass first time, which loop back, and which block. Nothing is sent anywhere. See [Measure your loops](guides/how-to/measure-your-loops.md).
- skilldrop is now dual-licensed: MIT or Apache-2.0, at your option.
## 0.14.0 — 2026-10-01

Eight new packs and 28 new skills (93 in all, across 17 packs). Install any pack with `npx skilldrop-cli install --pack <name>`; each brings `core`.

- **converters**: `md-to-docx`, `md-to-xlsx` and `md-to-html` turn Markdown into Word, Excel and a self-contained HTML file, in your brand.json's fonts and colours. Excel cells are typed, so numbers, percentages and dates sort and sum. `file-to-markdown` turns .docx, .pptx, .xlsx, HTML, CSV and JSON back into Markdown, and lists what it dropped. `mermaid-render` finds the errors that stop a Mermaid diagram rendering, with the line, then renders it. All of them are standard-library scripts, with nothing to install.
- **experience-design**: `information-architecture`, `ux-writing`, `content-design` (with a readability check on the before and after), `design-system-spec` and `service-blueprint`.
- **research**: `research-plan`, `source-synthesis` (a script checks that every claim cites a listed source) and `hypothesis-comparison` (competing explanations ranked by how little evidence contradicts them).
- **trackers**: `backlog-triage` finds duplicates, missing owners and acceptance criteria, and stale items in a Jira, Linear or GitHub export. `team-status-report` builds a weekly status whose numbers come from the export, with the rule that set its RAG. `tracker-brief-sync` turns a PRD into importable issues and reports drift between the two.
- **data-analytics**: `metric-definition`, `sql-review` (correctness first: fan-out joins, NULLs, time zones, with corrected SQL) and `dashboard-spec`.
- **grc**: `dpia`, `soc2-evidence-map` and `risk-register`, which checks a register CSV and prints a heat map. They prepare material for a qualified reviewer; they aren't legal or audit advice.
- **infra-as-code**: `terraform-module` writes a module with secure defaults. `terraform-plan-review` reads `terraform show -json` and gives SAFE TO APPLY, APPLY WITH CARE or DO NOT APPLY, naming every destroy, replacement and widened permission.
- **skill-engineering**: `skill-author` writes a portable skill with evals for any tool. `skill-review` audits one, with a lint script, and ends READY, FIX FIRST or REWRITE.
- **sre-oncall** adds `delivery-metrics-report` (DORA's four metrics and flow metrics, computed from your deploy and incident exports) and `cloud-cost-review` (waste and savings in an AWS, GCP or Azure cost export, with savings computed from the bill's own rates). `capacity-cost-model` now covers forward-looking estimates only.
- Five new jobs to browse by on the site: design the experience, research a question, define and trust the numbers, manage risk and compliance, and build agent skills.

## 0.13.9 — 2026-10-01

- The `claude-api` pack is now **`api-builder`**, because Claude Code now rejects plugin names that start with `claude-`, which could stop the whole marketplace from loading. Install it with `npx skilldrop-cli install --pack api-builder` or `/plugin install api-builder@skilldrop`. The old `--pack claude-api` still works, with a note, and the old pack page redirects. If you installed the `claude-api` plugin, uninstall it and install `api-builder`. The four skills are unchanged.

## 0.13.8 — 2026-10-01

- New install targets: `--ide codex`, `--ide antigravity` and `--ide copilot`. Each installs to the tool's personal skills folder, or into the repo with `--project` (`.agents/skills` for Codex and Antigravity, `.github/skills` for Copilot). `--panel review` works with all three.
- `--local` lets you try skills in a repo you don't own. It installs into the repo and lists every file in `.git/info/exclude`, so `git status` stays clean and nothing can be committed by accident. `uninstall --local` removes both the files and the entries.
- `--dry-run` on `install`, `update`, `uninstall` and `new-skill` shows exactly what would change, including which of your edited files would be overwritten, and changes nothing.
- `uninstall` and `update --force` ask before going ahead when you're at a terminal, and name any files you edited. `--yes` skips the question; scripts and CI are never asked.
- `skilldrop diff <skill>` shows how your installed copy differs from the catalogue's, file by file: your edit, a catalogue change, or both.
- `skilldrop doctor` checks an install against its ledger and reports missing skills, `.upstream` files waiting to be merged, and leftover wiring or hooks, each with the command that fixes it. It changes nothing.
- `skilldrop new-skill <name> --pack <pack>` scaffolds a skill with `SKILL.md`, `manifest.json` and both eval files, and registers it in `model-routing.json`. `skilldrop --version` prints the version.
- `skilldrop scan` tags each finding with its OWASP Agentic Skills Top 10 and LLM Top 10 2025 IDs. It now scans every markdown file in a skill, not only `SKILL.md`, and flags a skill that tells the agent to fetch instructions from a URL at run time. `update` scans skills from third-party catalogues again after updating them. [skilldrop and the OWASP Top 10s](guides/reference/owasp-mapping.md) maps each control and names the gaps.
- `agent-threat-model` tags every 🟥 and 🟧 path with its OWASP IDs, from a mapping table in its reference.
- Every skill now ships acceptance evals and trigger queries. The 14 that had none got them, and `validate.py` now requires both files. A new page on the site, *How skills are checked*, lists each skill's evals, and each skill page shows its assertions and trigger queries.
- A weekly workflow runs the trigger queries against a live model and reports which ones go to the wrong skill. It's report-only and needs an `ANTHROPIC_API_KEY` secret. `python3 run_evals.py` runs the same check locally, and `--assertions` grades the acceptance evals too.
- The repo is now a GitHub Action: `uses: sananthanarayan/skilldrop@<sha>` with `skill: doc-critique` runs a skill on a pull request's diff, writes the result to the job summary, and can fail the check on a verdict. See [Run a skill in CI](guides/how-to/run-a-skill-in-ci.md).
- Each pack page has *A typical session*: what you bring, then each step's skill with what you type, what you get and where you decide.
- Every release has its own page at `changelog/<version>/`, and `changelog/feed.xml` is an Atom feed for feed readers and Slack.
- Issue templates for bugs and skill requests, and a pull request template with the pre-commit checklist.
- CI scans every push for secrets (gitleaks), workflow errors (actionlint) and workflow security problems (zizmor).
- A Homebrew formula and a PyPI wheel builder, in `packaging/`, for when the tap and the PyPI project exist.

## 0.13.7 — 2026-10-01

- `install --with-hooks` and `uninstall` work inside a git worktree or submodule, where `.git` is a file rather than a folder. Both crashed there before. The pre-commit reminder now goes wherever git reads hooks from, including a custom `core.hooksPath`.

## 0.13.6 — 2026-10-01

- New **design** pack: `npx skilldrop-cli install --pack design` gets on-brand decks and flyers, with `core`.
- `brand-kit` captures your brand once as a `brand.json`: logo files (and an on-dark version), colours as hex codes, heading and body fonts, voice, imagery, your PowerPoint template, contact details and footer. Every value says where it came from, and a checker tests text contrast and catches missing or SVG-only logos.
- `marketing-flyer` makes a print-ready flyer in your brand, for an event, launch, offer or hiring drive. It's one HTML file that saves to PDF (or exports with `--pdf`, and `--png` for square and story social sizes), in four layouts, with one call to action and only the facts you gave it.
- `deck-builder` asks for your branding before it builds, and takes `--brand brand.json`. Without a template, it now puts your logo on every slide (the white version on dark slides) and uses your heading and body fonts. It and `slide-outliner` moved to the design pack; install them by name or with `--pack design`.

## 0.13.5 — 2026-10-01

- Every skill has its own page on the site, at `skills/<name>/`. Each page has one install command, a realistic prompt to try, what a good result looks like, what it hands off to, and its source. Catalogue rows link to it.
- Pack pages lead with one install command and fold the alternatives under "Other ways to install". A summary box above it says when to use the pack, which jobs it covers, where a person decides (each human or review gate), and how big it is.
- The packs index groups packs by the job in front of you, so you can start from "decide what to build" rather than a role name.
- Every page on the site (home, packs, skills, catalogue, docs, changelog) has the same navigation, and a new "What's new" page renders every release.
- The README is a short router: one line per role pack, one install command and its starter prompt, then links. The full skill list, the loop reference with its diagrams, and every install route now live in the docs portal, which renders tables and diagrams.
- `contribution-wizard` now tells authors to add a new skill's row to the skill catalogue guide rather than the README.

## 0.13.4 — 2026-10-01

- `npx skilldrop-cli install --profile <name>` works. The npm package was missing `profiles.json`, so profiles only worked from a clone of the repo.

## 0.13.3 — 2026-10-01

- Every pack now has a page with what to try first: a starter prompt to paste, how to tell it worked, and what to do if nothing happens. Browse them at `sananthanarayan.github.io/skilldrop/packs/`. The CLI prints the same starter after `install --pack`, or any time with `skilldrop info --pack <name>`, and each Claude pack plugin carries it in a README.
- Skills now live in their pack's folder: `packs/<pack>/skills/<name>/`, with loops at `packs/<pack>/loops/<name>/` and each pack's metadata in `packs/<pack>/pack.json`. To copy a skill by hand, use `cp -R packs/<pack>/skills/<name> ~/.claude/skills/`. Installs through the CLI, `pack.py` or the Claude plugins work as before, and `outdated` and `update` carry on across the move. An older CLI pointed at this repo with `--from` needs upgrading; flat `skills/` catalogs from other people keep working.
- `skilldrop install --profile <name>` works. It had been reading the profile name as missing.

## 0.13.2 — 2026-10-01

- `skilldrop update` no longer erases your edits to an installed skill. A file you changed is kept, and the new version is written next to it as `<file>.upstream` for you to merge. Files you didn't touch update as before, and `--force` still overwrites everything. Skills installed with an earlier version overwrite once on their next update, then keep edits from then on.
- Packs are re-cut so every skill and loop has exactly one home. A new `core` pack holds the skills every role uses (`brief-intake`, `doc-critique`, `output-hygiene`, `council-review`) and the `ship-a-draft` wrapper. Every role pack except `claude-api` installs `core` with it, through the CLI, `pack.py` and the Claude plugins alike, so one `--pack` command still gives a role its whole toolkit.
- Eight skills moved to a single pack: `user-story-splitter`, `launch-readiness` and `agents-md-generator` → `dev-team`; `capacity-cost-model` → `sre-oncall`; `data-contract` → `solution-architect`; `agent-threat-model` and `ai-use-case-triage` → `ai-engineering`; `exec-summary` → `stakeholder-comms`. If you installed a pack for one of these, install it by name or add the pack that now holds it.
- The `full` profile now includes every pack and every loop. It had been missing `claude-api` and `release`.

## 0.13.1 — 2026-10-01

- Run the new `release` loop to take merged code to live users: `migration-plan` plans the rollout and the rollback, `launch-readiness` judges readiness at G2.5, `release-notes` drafts the announcement, and a human makes the go/no-go call at G2.6. Install it with `skilldrop install --loop release`, or get it in the `dev-team` and `sre-oncall` packs.
- Ask "are we ready to launch?" and `launch-readiness` returns a go/no-go report: the change's own failure modes, then seven checks, each with evidence and an owner role. A missing rollback blocks the launch on its own, and detection or runbook gaps are handed to `observability-plan` and `runbook-generator`.

## 0.13.0 — 2026-09-30

- Browse every guide in a full docs portal at `sananthanarayan.github.io/skilldrop/docs/` — each of the 22 guides renders as a standalone HTML page with a persistent sidebar grouped by Diátaxis kind (tutorial, how-to, reference, explanation) and a live client-side search box that filters by title, summary, and body text.
- Install `skilldrop install --pack claude-api` to get four new skills for teams building on the Anthropic API: `prompt-caching-advisor` identifies where to insert `cache_control` checkpoints and estimates the cache hit rate; `token-budget-estimator` breaks down input/output token usage by workflow component and names the dominant cost driver; `eval-harness-generator` reads a SKILL.md and produces 8–12 eval cases covering happy path and edge cases; `tool-use-schema-writer` converts a plain-language function description into a valid Anthropic tool definition with a Python usage snippet.
- `contribution-wizard` guides an author through creating a new skill from scratch — one intake block generates the manifest, SKILL.md, eval cases, and README entry.
- Five new how-to guides cover integrating skilldrop with Jira, GitHub Projects, Figma, and Linear (which skills to use, what to paste, what to expect back), plus a credential brokering guide for skills that declare `env.required` — local shell, GitHub Actions secrets, and enterprise vault patterns.
- Two end-to-end scenario walkthroughs show the loops in action: "From complaint to closed incident" traces a Monday-morning support spike through the discover and operate loops with gate verdicts at each stage; "From idea to shipped feature" moves a product idea through all four lifecycle loops with a real refusal at every gate (G0 REVISE, G1 PROCEED WITH CONDITIONS, G2 BLOCKED, G3 postmortem delta).
- The catalogue site now has hero entrance animations, scroll-triggered reveals, animated stat counters that count up from zero on scroll, card hover lift, CTA glow, a nav logo shimmer, and a scroll-activated backdrop blur — all CSS and vanilla JS with no new dependencies.

## 0.12.2 — 2026-09-30

- `skilldrop bootstrap` writes the skilldrop marketplace into `~/.claude/settings.json` so
  every Claude Code session on the machine discovers the catalogue without any per-session
  `/plugin` command — one command for onboarding scripts or provisioning runbooks.
- The catalogue site now serves `marketplace.json` at a stable URL
  (`sananthanarayan.github.io/skilldrop/marketplace.json`) so org admins can point internal
  tooling at it directly.
- `pages` CI now guards `marketplace.json` against drift before deploying the site, so a
  stale marketplace is caught on PRs rather than after the merge.

## 0.12.1 — 2026-09-28

- `deck-builder` builds on your own PowerPoint template: point `template` at a `.potx`/`.pptx`
  and the deck inherits its masters, theme fonts, colours, logos and slide size. Discover the
  template's layouts with `build_deck.py --list-layouts brand.potx`, then bind each logical
  layout to one in `layout_map`. Placeholders are filled without flattening the brand's
  typography, and unfilled ones are deleted so no "Click to add text" ghosts survive.
- `deck-builder` gained three evidence layouts — `chart` (column, bar, line, stacked, pie,
  doughnut, with a required takeaway and source), `table` (styled header, zebra rows,
  auto-shrinking type), and `image` (aspect-fit, full-bleed or paired with bullets). A missing
  or non-raster image draws a labelled placeholder and warns instead of failing the build;
  `--strict` turns that into a hard error for CI.
- `deck-builder` asks for audience, format, time budget and design in **one** setup block with
  defaults pre-chosen, instead of asking about the palette alone — and honours `"aspect": "4:3"`
  for decks that aren't 16:9. Slide numbers appear automatically past 10 slides.

## 0.12.0 — 2026-09-25

The milestone the 0.11.6–0.11.9 releases were building toward.

- **skilldrop is an operating model now, not a catalogue.** Install one command and get a way of working — five loops over 57 skills, six named gates, one verdict vocabulary — instead of 57 things to choose between. A loop *orders* skills and never contains one, so all 57 still install and run alone by folder copy, and the whole thing still has zero runtime dependencies.
- **Five loops.** `discover` → `design` → `build` → `operate` cover the lifecycle and are separated by **reversibility** — a re-brief, months unwound in code, a revert, live users — which is also what decides whether a script, a review panel, or a person holds the gate. `ship-a-draft` wraps any generator. Install one with its stage skills: `skilldrop install --loop build`.
- **Gates that can actually refuse.** Six named gates (G0–G4) answering from one shared vocabulary in five classes, so `READY`, `PROCEED` and `SHIP IT` are recognisably the same kind of answer — and `validate.py` rejects a gate that can only succeed, one that cannot say `BLOCKED`, or one that invents a new word for an existing outcome.
- **Directed hand-offs with a mandatory `fallback`**, which turns "sibling hand-offs are advisory" from prose an agent may ignore into something the linter checks. 22 edges across 15 skills.
- **A closed contract per primitive** in `contracts/` — skills, packs, loops, agents, guides — checked by a ~50-line stdlib JSON Schema subset. `"tier": "claude-opus-5"` now fails the lint instead of only the style guide.
- **Docs a stranger can actually use:** `ARCHITECTURE.md`, a Diátaxis `guides/` tree with a full walkthrough tutorial, and a README down from 714 to ~525 lines.
- **`llms.txt`** so a model reads the handful of pages that matter instead of crawling 400+ files. Generated and drift-checked, because a stale index a model trusts is worse than no index.

New in this release specifically:

- New [`llms.txt`](llms.txt), generated from `packs.json`, the loop contracts, `contracts/` and guide frontmatter. Served from the repo root and the site root.
- The site leads with the operating model: new hero, **Loops** second in the nav and second on the page, **Outcomes** promoted from filter chips to a section, and a **Docs** section surfacing `ARCHITECTURE.md`, the guides and `llms.txt` — all previously near-invisible to a visitor.
- New tutorial: [Follow one change through the loops](guides/tutorial/follow-a-change-through-the-loops.md) — one realistic change from a stakeholder complaint to a closed incident, organised around what each gate refuses.
- All five loops ship acceptance evals — 10 cases, 35 trigger queries, shape enforced. Two encode failure modes a stage table cannot prevent: routing a revise to the wrong stage, and treating `PROCEED WITH CONDITIONS` as `PROCEED`.

## 0.11.9 — 2026-09-25

- Every primitive now has a **closed, machine-readable contract** in `contracts/` — skills, packs, loops, agents, and guides. `validate.py` checks each instance against its schema, so a typo'd manifest key fails instead of being ignored, and `"tier": "claude-opus-5"` is finally rejected by the lint rather than only by the style guide. Checked by a ~50-line stdlib JSON Schema subset: skilldrop still has zero runtime dependencies.
- New **`ARCHITECTURE.md`** — the four primitives, why a loop is not just a long skill, why the loops are separated by reversibility, the copy-never-transform install contract and its one exception, and the five invariants worth protecting.
- The README is 714 → 522 lines. Per-IDE install steps, hooks, catalogue publishing, script-shipping skills, and the authoring paths moved into **`guides/`**, split by Diátaxis kind declared in frontmatter rather than by directory. A guide that is not linked from `guides/README.md` fails the lint, because an unindexed guide is unfindable.
- New guides for authoring: [Author a new loop](guides/how-to/author-a-loop.md) and [Why loops](guides/explanation/loops.md), which explains why sequencing is its own primitive and why there are four lifecycle loops rather than three.
- Fixed a blank line that made the reviewer-agents table render as two broken tables on GitHub.

## 0.11.8 — 2026-09-25

- Loops are installable: `skilldrop install --loop build` puts the loop *and* every stage skill it sequences into your tool in one command. `--no-skills` installs the loop alone — it still runs, because each stage degrades through its declared `fallback`. `--loop --pack sre-oncall` installs every loop a pack declares.
- `skilldrop loops` lists the five loops with their stages and gates; `--json` emits the whole shape for tooling. `skilldrop uninstall --loop <name>` removes a loop and leaves its stage skills in place.
- A loop installs as an ordinary invokable skill. `LOOP.md`'s frontmatter is already `SKILL.md`'s shape, so it projects to `<dest>/<name>/SKILL.md` with `loop.json` beside it — no target needs a loop primitive of its own.
- Role packs now declare their loops, so `dev-team` brings `build`, `sre-oncall` brings `operate`, and `product-manager` brings `discover`. `validate.py` checks both directions, and refuses a loop whose name collides with a skill's.
- The catalogue site gained a **Loops** section, a loops stat tile, and a `loops` key in `catalogue.json`.
- Per-pack Claude Code plugins now carry their pack's loops, so `/plugin install sre-oncall@skilldrop` brings the `operate` loop with the runbook and incident skills it sequences.

## 0.11.7 — 2026-09-25

- Three more loops complete the lifecycle: `discover` (raw signal to a requirement a human ratifies at **G0**), `design` (a requirement to a recorded ADR, gated by `council-review` at **G1**), and `operate` (a shipped service through detection, response and learning at **G3**). With `build` and the `ship-a-draft` wrapper, skilldrop now ships five loops.
- The four lifecycle loops are separated by **reversibility** — a discovery mistake costs a re-brief, a design mistake is unwound in code months later, a build mistake is a revert, an operate mistake reaches live users — which is why each owns its own gate instead of folding into a neighbour.
- `operate` closes a real feedback edge: `postmortem-generator` emits runbook deltas and the loop routes them straight back into `runbook-generator`.
- Skills can now declare a **directed** hand-off: `handoff: [{ to, when, purpose, fallback }]`. `fallback` is required, which turns "sibling hand-offs are advisory" from prose into something `validate.py` checks — a hand-off to a skill you have not installed now degrades in a stated way instead of dead-ending. 22 edges ship across 15 skills.
- Loop diagrams are generated from `loop.json` by the new `build_loops.py`, into `docs/loops/*.mmd` and the README's mermaid blocks. `validate.py` fails on drift, so a diagram can no longer disagree with the contract it illustrates. The two hand-maintained `.mmd` files this replaces are retired.

## 0.11.6 — 2026-09-25

- skilldrop now ships **loops**, not just parts. A loop is a named sequence of stages over existing skills with a gate between them — `loops/build/` takes an agreed requirement to merged code behind a mechanical gate, and `loops/ship-a-draft/` wraps any generator in structured intake before and critique plus a machine-residue scrub after (RFC-0028).
- A loop sequences skills but never contains one, so all 57 skills stay independently installable and a single-folder copy still works in Cursor, Kiro, and Aider.
- Every gate now answers from one shared verdict vocabulary (`contracts/terminals.json`) in five classes — pass, conditional, revise, redirect, blocked — instead of each skill inventing its own word for the same outcome.
- The two pipeline diagrams that lived only as README prose are now backed by machine-readable `loop.json` contracts that `validate.py` enforces: named skills must exist, gate ids are repo-unique, a mechanical gate's script must be real, and a gate that can only succeed is rejected.

## 0.11.5 — 2026-09-18

- Role packs are now installable as Claude Code plugins: `/plugin install solution-architect@skilldrop` after the same one-line `marketplace add`. A pack carries the reviewer subagents its own skills delegate to, so `dev-team` brings the review panel and `sre-oncall` does not (RFC-0027).
- Retired the generated `agentbundle-catalogue` branch and its exporter. It was never documented as an install path, and its publish was gated by a third-party verifier that had moved 24 minor versions since the export was written. Reading agentbundle-shaped catalogues with `skilldrop --from <repo>` is unaffected.
- The README skill-count guard no longer misfires on per-pack counts inside a code block.

## 0.11.4 — 2026-09-18

- New skill `output-hygiene`: finds what a machine left in agent-written text — invisible Unicode, non-breaking spaces, homoglyphs, harness-added provenance trailers, trailing chat closers — and separates what is safe to strip from what needs a decision (RFC-0025).
- The catalogue page now opens with its search box and filters visible instead of hiding all 57 skills behind a disclosure toggle (RFC-0026).
- Filter state lives in the URL, so a filtered view — one pack, one tier, one outcome — is a link you can send someone.
- New browse axis: seven **outcomes** answer "why am I here", alongside the six role packs that answer "who am I".
- The site shows its own version and its three most recent releases, so a visitor can tell the project is alive.

## 0.11.3 — 2026-08-10

- `validate.py` fails when a shipped skill has no README row, so the catalogue can no longer document less than it ships.
- Every RFC carries an accurate status, and the pre-commit checklist says which rules are machine-enforced and which are human judgment.

## 0.9.3 — 2026-08-07

- New skill `agent-adoption-stage`: places a team on an agent-adoption curve and names the next move (RFC-0024).

## 0.9.2 — 2026-08-07

- Four AI-adoption skills: `ai-readiness-assessment`, `ai-use-case-triage`, `ai-adoption-rollout`, `ai-usage-policy` (RFC-0023).

## 0.9.1 — 2026-08-06

- `skilldrop` read commands take `--json` (RFC-0021), so the catalogue is scriptable.
- Supply-chain scanning on the code that runs on other people's machines (RFC-0022).
- Evals backfilled across the activation-collision clusters that actually compete.

## 0.9.0 — 2026-08-05

- `skilldrop install --panel review` installs the whole reviewer panel in one command (RFC-0020).
- Model map refreshed to the Claude 5 family; conformance to the Agent Skills open standard declared.
