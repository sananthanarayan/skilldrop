---
name: subagent-design
description: Decompose a task into an orchestrator and subagents — one-mission role cards with typed output contracts, a topology (pipeline / parallel / judge panel) chosen with a reason, context-isolation rationale, and a verification stage that is never a generator. Use when the user wants to fan work out across multiple agents, design a multi-agent workflow or orchestration, or asks "should this be one agent or several".
---

# subagent-design

Produces an **orchestration plan**: which subagents exist, what each one alone is for, how their outputs compose, and who checks the result. The default answer to "should this be several agents?" is **no** — one context that fits is always simpler; fan out only when a plan survives step 1. Two skilldrop skills are ready-made instances of the patterns worth copying — `council-review` (a judge panel of independent perspectives) and `devils-advocate` (an adversarial verifier that isn't the generator) — cite them as patterns even where they aren't installed. Loop mechanics around the fan-out belong to `agent-loop-design`; what the fleet may spend belongs to `agent-budget`.

## How to respond

1. **Justify the fan-out or refuse it.** Exactly three reasons earn multiple agents — name which applies, or recommend a single agent and stop:
   - **Context separation**: the task spans more material than one context holds well, and it partitions cleanly (per-module audit, per-source research).
   - **Independence**: judgments must not contaminate each other — reviewers, estimators, hypothesis-testers whose value is that they haven't seen each other's answers.
   - **Role conflict**: one agent can't hold both jobs honestly — the generator must not grade itself; the negotiator must not also be the auditor.

   "It would be faster" alone is not on the list — parallelism is a consequence of separation, not a reason to manufacture it. Non-interactive run (no user to ask): derive the task from the input, tag assumptions `[assumption]`; no task derivable → emit `BLOCKED: need the task being decomposed`.

2. **Write one role card per agent** — the plan's core, using [`templates/orchestration-plan.md`](templates/orchestration-plan.md). Each card: **mission** (one sentence, one job — an agent with "and" in its mission is two agents or one agent over-split; a mission repeated across items is one card with a ×N multiplier, and splitting one item's work into separate per-check cards is worth the extra invocations only when the isolation or tier difference pays for it), **inputs** (exactly what it's given — and, as important, what it's *denied*: the context-isolation line states what this agent must not see, e.g. a judge never sees the other judges' verdicts), **output contract** (a typed schema — fields and types, not "a summary"; prose outputs make aggregation a second AI task you didn't budget), **tools/permissions** (least privilege: a research agent gets read, never write), and **failure behavior** (what it returns when it can't do the job — a structured `BLOCKED`/empty result, never improvisation).

3. **Pick the topology, with the reason attached:**
   - **Pipeline** — stages feed forward; item B needn't wait for item A's later stages. The default for multi-stage work.
   - **Parallel + barrier** — only when a stage genuinely needs *all* prior results at once (dedup across findings, a zero-count early exit). A barrier "because the stages feel separate" burns wall-clock for tidiness.
   - **Judge panel** — N independent attempts or verdicts, then score/merge (`council-review`'s shape). For wide solution spaces and contested judgments; specify the vote rule (majority, unanimous-to-kill) up front.
   - **Depth cap: one level.** Subagents spawning subagents needs a written justification; two levels of delegation is where accountability and budgets go to disappear.

4. **Design the aggregation and verification stage.** Aggregation is code-shaped where possible (merge schemas, dedup by key) — an "aggregator agent" summarizing prose is a smell that the output contracts were too loose. Verification is a **separate stage with an adversarial job description** (`devils-advocate` framing): it tries to refute, and its verdict gates the result. The orchestrator trusts contracts, not content — a subagent's confident prose is not evidence; count only schema-valid outputs, and route contract violations to the failure path, never into the merge.

5. **Attach the budget line and emit.** Per-agent tier (light/standard/heavy — the repo's routing abstraction; most fan-out workers are one tier below the orchestrator's instinct) and the fleet's cap per run, referencing an `agent-budget` spec or tagging the numbers `[assumption]`. Emit in one message: fan-out justification, role cards, topology (Mermaid `flowchart`) with the reason, aggregation + verification, budget line. Hand off: the loop around this fan-out → `agent-loop-design`; the full spend model → `agent-budget`; implementing a coding task through it → `feature-implement-loop`.

## Useful references in this skill

- [`templates/orchestration-plan.md`](templates/orchestration-plan.md) — role cards, topology diagram, aggregation/verification, budget line

## Quality bar

- **The fan-out is justified by one of the three reasons, by name** — or the plan says "one agent" and means it.
- **Every mission is one sentence with no "and".** Two jobs, two cards.
- **Every output contract is typed.** A reader could write the JSON schema from the card.
- **Isolation lines are explicit** — each card says what the agent is denied and why.
- **The topology has its reason attached**, and any barrier names the cross-item dependency that earns it.
- **Verification is adversarial and separate** — never the generator, never "the orchestrator double-checks".
- **The budget line exists** — per-agent tier + fleet cap, sourced or tagged.

## When to use this skill

- ✅ "Should this be one agent or several?" — including when the honest answer is one
- ✅ Designing a multi-agent review, audit, research sweep, or migration
- ✅ A fan-out exists but produces mush — retrofit contracts, isolation, and verification
- ✅ Choosing between pipeline, barrier, and judge-panel shapes for a workflow

## When NOT to use this skill

- ❌ Designing the loop that wraps the fan-out (caps, gates, exits) — `agent-loop-design`
- ❌ Setting the spend policy — `agent-budget`
- ❌ Running a multi-perspective review right now — `council-review` is the panel, ready-made
- ❌ Implementing one story — `feature-implement-loop`

## Anti-patterns to avoid

- ❌ **Fan-out as a lifestyle.** Five agents doing what one context does well is five times the cost for a coordination tax. The burden of proof is on splitting.
- ❌ **Prose contracts.** "Each agent reports its findings" guarantees an unmergeable pile and a surprise summarization stage. Schemas or it didn't happen.
- ❌ **Contaminated judges.** A panel that sees each other's verdicts is one opinion with extra steps — independence is the entire value.
- ❌ **The trusting orchestrator.** Merging whatever comes back because it arrived confidently. Contract-invalid output goes to the failure route, not the report.
- ❌ **Unbounded depth.** Subagents spawning subagents until nobody can say who decided what or spent which tokens.
- ❌ **Barrier by aesthetics.** Synchronizing stages because the diagram looks cleaner — pay wall-clock only for a named cross-item dependency.
- ❌ **Verifier-free fleets.** Ten generators and no refuter ships ten agents' worth of plausible-but-wrong at fleet speed.
