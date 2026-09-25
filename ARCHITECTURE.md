# Architecture

How skilldrop is put together, and which properties are load-bearing. For *what to do* when
adding something, see [AGENTS.md](AGENTS.md); for the decision behind any given rule, see
[docs/rfcs/](docs/rfcs/).

## The shape in one paragraph

skilldrop is a **catalogue of portable agent instructions plus an operating model over them**.
Four primitives live in flat top-level directories, each installed by copying a folder. There
is no runtime, no server, and no dependency: `validate.py` and `build_*.py` are stdlib-only
Python, [`bin/skilldrop.js`](bin/skilldrop.js) is stdlib-only Node, and `package.json` has no
`dependencies` block. What runs in a user's IDE is byte-identical to what is reviewed here.

## The four primitives

| Primitive | Lives in | Is | Installed as |
|---|---|---|---|
| **Skill** | `skills/<name>/SKILL.md` + `manifest.json` | One artifact generator or reviewer. Self-contained. | folder copy, verbatim |
| **Loop** | `loops/<name>/LOOP.md` + `loop.json` | An ordered sequence of stages over skills, with a gate between them | `<dest>/<name>/SKILL.md` + `loop.json` |
| **Pack / outcome** | `packs.json` | Metadata only. Packs say *who* needs a skill; outcomes say *why*. | not installed — expands to a skill list |
| **Agent** | `agents/<name>.md` | A reviewer subagent: frontmatter + a system prompt | projected per target |

Contracts for all four are machine-readable in [`contracts/`](contracts/), and
`validate.py` checks every instance against them with a hand-rolled JSON Schema subset.

### Why a loop is not just a long skill

The rule that makes the catalogue portable is that **a skill never invokes a skill**. A
chained skill stops working the moment someone installs it alone into Aider, which destroys
the one advantage skilldrop has over heavier agent platforms.

So sequencing moved **up**, not sideways. A loop owns the order; skills stay standalone. A
skill may *declare* a directed `handoff` — but the loop, or a human, is what acts on it.

`LOOP.md`'s frontmatter is deliberately identical to `SKILL.md`'s (`name` + `description`),
which is why a loop installs into the skills directory and becomes invokable with no target
needing a loop primitive of its own. The cost of that choice: loops and skills share one
namespace, so `validate.py` refuses a name collision.

### The four loops are separated by reversibility

Not by team, not by phase. The question is *how expensive is the mistake to unwind* — which
is also what determines who is allowed to decide:

| Loop | Mistake costs | Gate |
|---|---|---|
| `discover` | a re-brief | **G0** human |
| `design` | months, unwound in code | **G1** review panel |
| `build` | a revert | **G2** mechanical |
| `operate` | live users; irreversible | **G3** human |

`ship-a-draft` is a **wrapper**, not a lifecycle stage: its middle is any generator, chosen at
run time. Every gate answers from one shared vocabulary
([`contracts/terminals.json`](contracts/terminals.json)) in five classes — pass, conditional,
revise, redirect, blocked — so a gate cannot invent a new word for an outcome that has one.

## The install contract

**Copy, never transform** — for skills and loops. `cpSync` of a directory, plus a ledger
entry. No templating, no substitution. This is what lets the repo claim that the reviewed
artifact and the running artifact are the same bytes.

**Agents are the one exception.** Every target expects a different agent format, so
`writeAgent()` projects `agents/<name>.md` into Kiro JSON, Codex TOML, Copilot `.agent.md`,
or plain markdown. Projection is confined to that function; nothing else in the CLI
transforms content.

**Wiring is separate from copying.** Where a target cannot discover a skill by path (Cursor),
the CLI writes a small pointer file. It is tracked so `uninstall` can remove it.

**The ledger** (`.skilldrop.json`, one per destination) records `{version, source}` per
installed unit, which is what makes `outdated` and `update` possible — `cp -R` never tells
you a skill improved.

## Enforcement

Conventions that live only in prose rot. The split is deliberate and stated honestly in
AGENTS.md: what is mechanical, and what is human judgment.

| Layer | Runs | Checks |
|---|---|---|
| `validate.py` | locally + every PR | contracts, name triples, two-way pack/outcome/loop membership, `related` ↔ SKILL.md sync, `handoff` ⊆ `related`, tier sync, gate/verdict rules, reference + link integrity, README coverage |
| `node bin/skilldrop.js validate` | locally + every PR | structural check from the *installer's* point of view — including third-party catalogues |
| `build_loops.py --check` | via validate.py | generated diagrams match `loop.json` |
| `build_marketplace.py --check` | via validate.py + `plugins.yml` | committed `.claude-plugin/` matches its generator |
| `build_site.py --check` | `pages.yml` | the rendered catalogue matches the manifests |

**One declared producer per generated path.** `docs/loops/*.mmd` and the README's Mermaid
blocks both come from `loop.json`; `.claude-plugin/` comes from `package.json` + `packs.json`.
Hand-editing any of them fails a check. This rule exists because the repo previously carried
two `.mmd` files that duplicated two README blocks with no producer relationship — editing
one silently left the other stale.

## Invariants worth protecting

1. **Zero runtime dependencies.** The most valuable property here. A contributor's PR goes
   green with no provisioning, and `npx skilldrop-cli` cannot break on a transitive update.
   If a contract needs a JSON Schema keyword the checker lacks, teach the checker.
2. **Offline and deterministic.** No check makes a network call. `route.py` decides a model
   tier from stored rules rather than asking a model, because the right tier for a skill is
   stable and paying tokens to re-derive a fixed answer is waste.
3. **A skill runs alone.** Every hand-off degrades through its declared `fallback`; a missing
   sibling is never an error.
4. **Tiers are abstract.** `light` / `standard` / `heavy` only. Concrete model names live in
   exactly one place — the provider map in [`model-routing.json`](model-routing.json).
5. **Generated output is never committed by hand**, and `build/` is not committed at all.

## Repository map

```
skills/       57 skills            loops/        5 loops
agents/       3 reviewer subagents contracts/    machine-readable schemas
packs.json    packs + outcomes     model-routing.json  tier per skill + provider map
bin/          the CLI              guides/       Diátaxis how-to / reference / explanation
docs/rfcs/    decisions            docs/loops/   generated diagrams
build_site.py build_marketplace.py build_loops.py  validate.py  route.py  pack.py
```

Anything outside `skills/`, `loops/`, `agents/`, and `contracts/` is repo policy or hygiene.
A new top-level directory needs an RFC.
