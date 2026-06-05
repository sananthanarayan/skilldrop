# Model routing — cost-aware, provider-neutral model selection per skill

This repo ships a **routing layer** that picks the most cost-effective model for each skill — and it's **not tied to Claude Code**. Skills declare an *abstract tier* describing how much reasoning the task needs; a `providers` map resolves that tier to whatever model your tool (Claude Code, Cursor, Codex, Kiro, …) actually exposes. Switch tools by changing one field.

The premise: *the right tier for a skill is stable* — `devils-advocate` always wants deep reasoning; `decision-log` never does. So the tier is decided **once per skill** and stored, instead of being re-derived by an LLM on every call (which would cost tokens + latency to answer a question that barely changes).

## The three abstract tiers

Tiers describe the **task**, not a vendor's model:

| Tier | For | Illustrative cost |
|---|---|---|
| 🟢 **light** | Mechanical mapping / extraction against a fixed rubric — a small model matches a large one here. | 1× |
| 🔵 **standard** | Most generation: synthesize a structured artifact from a brief. The default. | ~4× |
| 🟣 **heavy** | Adversarial reasoning + weighted judgment, where a cheaper model demonstrably misses things. Never downgraded. | ~20× |

## Picking your tool (the `providers` map)

`model-routing.json` has a `providers` section that maps each tier to a concrete model **per tool**, and an `active_provider` field. To use a different tool:

1. Open `model-routing.json`.
2. Find your tool under `providers` (or use `generic`). Fill in its `light` / `standard` / `heavy` model names with the models your plan exposes — the placeholders `<...>` are there for you to replace.
3. Set `active_provider` to your tool's key.

Shipped providers (Claude Code is filled in; the rest are templates you complete):

| Provider key | Tool | Models | How you select a model |
|---|---|---|---|
| `claude-code` | Claude Code | ✅ filled in (Haiku / Sonnet / Opus 4.x) | `/model <id>`, or the router agent (automatic) |
| `cursor` | Cursor | ⬜ fill in | Model dropdown in the chat/composer pane |
| `openai-codex` | OpenAI Codex CLI | ⬜ fill in | `--model` flag / config |
| `kiro` | Kiro | ⬜ fill in | Model picker, or pin in the custom-agent/steering def |
| `generic` | Anything else | ⬜ fill in | However your tool selects a model |

> **Why templates instead of pre-filled model names?** Model identifiers churn fast and differ by tool and subscription. The tier abstraction is stable; the concrete name is yours to set. We fill in only what we can verify (Claude Code) and leave the rest editable rather than ship names that go stale or don't match your plan.

## Per-skill assignments

### 🟢 light — mechanical
| Skill | Why |
|---|---|
| `audience-profile` | Maps fixed audience archetypes to structural rules. Lookup, not synthesis. |
| `decision-log` | Extracts decisions/owners/dates from notes. Pattern extraction. |
| `sonar-onboard` | Scaffolds config from detected language + template. Deterministic fill-in. |

### 🔵 standard — generation (the default)
| Skill | Why |
|---|---|
| `adr-generator` | Structures a decision into MADR/Nygard. Bounded judgment. |
| `architecture-diagrams` | Prose → diagram syntax. Correctness matters, reasoning bounded. |
| `brief-intake` | Extraction + `[explicit]/[implied]/[inferred]` tagging. Tagging needs care. |
| `deck-builder` | Generates pptx content + runs a script. Content shaping. |
| `design-doc` | Synthesizes a design doc. *Escalates to heavy* on big/contested inputs. |
| `exec-summary` | One-page compression. *Escalates* on very long source docs. |
| `figma-diagrams` | API calls + spec generation. Bounded transformation. |
| `guide-builder` | Shapes notes into a styled guide. |
| `reverse-architecture` | Extracts architecture from code/IaC. *Escalates* on large codebases. |
| `runbook-generator` | Operational doc from service facts. |
| `slide-outliner` | Outlines a deck to a time budget. |
| `sonar-review` | Formats Sonar API findings into a report. The hard analysis is Sonar's. |
| `ai-usage-report` | Tabulates telemetry; the "AI theater" call needs some judgment. |

### 🟣 heavy — reasoning (never downgraded)
| Skill | Why |
|---|---|
| `devils-advocate` | Adversarial code review. Cheaper models miss edge cases + under-call severity. |
| `doc-critique` | Adversarial doc review. The value is catching what a fast pass misses. |
| `tech-comparison-matrix` | Weighted multi-criteria judgment. Mis-weighting is the failure mode. |

## Escalation rules (mechanical — no LLM call)

The declared tier is the **starting point**. These rules adjust it from cheap signals, never from an LLM judgment:

1. **`user-override`** *(hard)* — an explicit model choice always wins. The router still reports what it *would* have picked.
2. **`reasoning-floor`** *(hard)* — never downgrade a `heavy` skill. Upgrade-only.
3. **`large-input`** — input > ~30 pages / ~20k words / ~15 files ⇒ **escalate one tier**.
4. **`ambiguous-input`** — contradictory/underspecified input, or an explicit ask for rigor ⇒ **escalate one tier**. Not just because the topic *sounds* important.
5. **`downgrade-trivial`** — tiny templated input ⇒ **downgrade one tier**, never below `light` and never below the skill's floor.

## How to use it

**Manual (any tool):** look up the skill's tier here → look up your tool's model for that tier in `model-routing.json` → set that model → invoke the skill. Three lookups, zero runtime cost.

**Automated (Claude Code only, today):** hand the work to the router agent —

> Use the model-router agent to run `decision-log` on these meeting notes: …

It prints its decision (`Routing decision-log → light / claude-haiku-4-5 (declared tier: light)`), then runs the skill on a subagent at the resolved model and returns the artifact. Other tools don't have a subagent-with-model-override primitive yet, so they use the manual path — but they read the **same table**, so the routing decisions are identical.

## `route.py` — pure-rules engine (no API key, no network, instant)

For deterministic, offline routing — usable from any tool, a CI step, or a git hook — the repo ships [`route.py`](route.py). It's the escalation rules as plain Python: **keyword + length signals with small, transparent weights you tune at the top of the file.** No model call, no key, no network.

```bash
python3 route.py --skill devils-advocate --input diff.txt
git diff | python3 route.py --skill sonar-review --files 12
python3 route.py --skill exec-summary --text "summarize for the board" --json
python3 route.py --skill design-doc --input brief.md --provider cursor
python3 route.py --list          # every skill + its declared tier
```

It prints the declared tier, the final tier, the resolved model for the active (or `--provider`) tool, and **every signal that fired with its weight**, so the decision is fully auditable:

```
decision-log: light → heavy
  model:     claude-opus-4-8  (provider: claude-code)
  signals (net +2):
    +1  explicit-rigor('thorough')
    +1  high-stakes-context('board')
```

**How the score works** (all knobs live at the top of `route.py`):
- Each skill starts at its **declared tier**.
- **Structural signals** (size-based, reliable): > ~20k words or ≥ 15 files ⇒ `+1`; ≤ 60 words and nothing escalating ⇒ `−1` (trivial).
- **Keyword groups** (wording hints): `explicit-rigor`, `high-stakes-context`, `security-sensitive`, `ambiguous-input` each add `+1` (once per group); `trivial-intent` adds `−1`.
- Net score is clamped to **`+2` / `−1`** so stacking can't run away, then applied up/down the ladder.
- **Hard rules still win:** a `heavy` skill is never downgraded; `--tier` forces a tier (and reports what the rules *would* have picked).

Tuning is just editing the weights/keyword lists at the top — no engine changes. Two keyword groups firing together can lift `light → heavy`; if that's too aggressive for your taste, lower `MAX_STEP_UP` or the group weights. That's the intended knob.

The `model-router` agent runs `route.py` when it's present (free + deterministic) instead of eyeballing the input — so the agent and the CLI agree by construction.

## Implementing automation in another tool

The router agent is just one implementation of a simple spec. The shortest path in **any** tool is to shell out to `route.py` — it already does steps 1–3 with zero cost:

```bash
TIER=$(python3 route.py --skill design-doc --input brief.md --json | jq -r .final_tier)
MODEL=$(python3 route.py --skill design-doc --input brief.md --json | jq -r .model)
# then set $MODEL in your tool and run the skill
```

Or implement it natively in the tool's extension/agent model:
1. Read `model-routing.json`.
2. Look up `skills.<name>.tier`; apply `escalation_rules` (pure heuristics, no model call) — or just call `route.py`.
3. Resolve `providers[active_provider].models[<tier>]`.
4. Set that model and run the skill.

The spec is provider-neutral on purpose — porting the automation is a small adapter, not a rewrite.

## Why not a live classifier on every call?

Because it's anti-cost-effective. Running an LLM to decide "light or standard?" on every invocation pays tokens + latency *every time* to answer a question whose answer is fixed per skill. The expensive, variable part of a task is the **work**, not the **routing** — so routing is a free table lookup and the model budget is spent on the work. The only things that genuinely vary per call (input size, ambiguity) are handled by cheap mechanical heuristics, not a model.

## Keeping this in sync

`model-routing.json` is the **source of truth**; this file is the human-readable view. When you add a skill, add its tier to both, and add a `model` block to its `manifest.json` (so the hint travels when the skill is copied into another IDE). See [AGENTS.md](AGENTS.md#model-routing).
