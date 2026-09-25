# Changelog

What shipped in each released version of `skilldrop-cli`. The site reads the newest three
entries into its **Recently shipped** section (RFC-0026), and `build_site.py` refuses to
build if the version at the top of this file disagrees with `package.json` — so a release
cannot ship undocumented.

Format: `## <version> — <YYYY-MM-DD>`, newest first, one bullet per user-visible change.
Bullets say what a user can now do, not which files moved.

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
