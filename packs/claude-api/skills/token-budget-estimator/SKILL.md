---
name: token-budget-estimator
description: Estimates input and output token usage for a described agentic workflow, surfaces the dominant cost drivers, and suggests max_tokens budget controls per component. Use when planning a new Claude API integration, sizing a cost budget for a feature, or diagnosing why a workflow's token usage is higher than expected.
---

# token-budget-estimator

Breaks down token usage for an agentic workflow — before you build it or while diagnosing runaway costs. The output is a component table (not a single number) because "how many tokens does this use?" has a different answer for the system prompt, the growing context window, tool results, and the final output. Knowing which component dominates tells you where to optimize.

## How to respond

### Step 1 — Intake

Ask the user to describe their workflow. Collect:
- What the agent does (brief description)
- The shape of the system prompt (static instructions, injected context, few-shot examples — rough character/word count is fine)
- How many turns or tool calls a typical session has
- What tool results look like (small JSON blobs? Full document retrieval? Database rows?)
- Roughly how long the final output is

If they already have working code or logs, ask them to share a sample API request/response — you can count tokens more accurately from the actual content.

### Step 2 — Estimate each component

Build a token budget table. Token approximation: **1 token ≈ 4 characters** of English text; code/JSON runs denser (~3 chars/token).

| Component | Est. tokens | Notes |
|---|---|---|
| System prompt | X | Static — same every call |
| Injected context (per call) | X | User data, retrieved docs, etc. |
| Few-shot examples | X | Static — cache candidate |
| User turn (per call) | X | Variable per request |
| Tool definitions | X | Sent on every call that uses tools |
| Tool results (per turn) | X | Accumulate across turns |
| Context accumulation | X | Previous turns retained in window |
| Output (per call) | X | Depends on max_tokens and task |
| **Total per session** | X | Sum across all turns |

Flag the **dominant cost driver** — the single row with the largest token count — and explain why it dominates.

### Step 3 — Recommend budget controls

For each component, suggest a concrete control:

- **System prompt too large**: split static vs dynamic; cache the static portion (`prompt-caching-advisor`)
- **Context accumulation**: summarize earlier turns, or use a sliding window instead of full history
- **Tool results**: truncate or paginate large results before passing to the model; never inject a 50-row database result when 5 representative rows suffice
- **Output**: set `max_tokens` to the realistic output ceiling — open-ended `max_tokens` on a generation task wastes budget on over-generation
- **Tool definitions**: only send the tools relevant to the current task state (tool selection narrows with progress)

### Step 4 — Extended thinking note

If the workflow uses extended thinking (`betas: ["interleaved-thinking"]`), add a note: thinking tokens are billed at the same input rate and are subject to a `budget_tokens` cap you set. Recommend setting `budget_tokens` to 2–4× the typical output length for reasoning tasks, and lower for classification or extraction tasks where long thinking chains rarely help.

### Step 5 — Output format

Produce:
1. **Token budget table** — the component breakdown with estimates
2. **Dominant driver** — named and explained
3. **Three concrete controls** — ranked by expected savings, with specific API parameters where applicable (`max_tokens`, `cache_control`, tool selection logic)
4. **Rough cost estimate** — using current public pricing for the tier the user is on (state the tier assumption; don't guess if unknown)

## Anti-patterns

- **A single total without a breakdown.** "~50,000 tokens per session" tells a developer nothing actionable. Always produce the component table.
- **False precision from descriptions.** "3,142 tokens" from a description is theatre. Use ranges; tighten only when working from actual content.
- **Optimizations without a ranking.** Listing five suggestions without saying which saves the most wastes the developer's attention.

For caching-specific advice after sizing the budget, hand off to `prompt-caching-advisor`. For agent-level spending controls, see `agent-budget`.

## Quality bar

- **Ranges over false precision.** "~2,000–4,000 tokens" is more honest than "3,142 tokens" when you're working from a description. Use ranges when working from descriptions, tighter estimates when working from actual content.
- **The table beats the total.** A single "~50,000 tokens per session" is nearly useless — the table that shows context accumulation accounts for 40,000 of those gives the developer somewhere to act.
- **Name the optimization target.** Don't list five optimizations without ranking them. The one that saves 80% of the dominant component beats the one that shaves 5% off a small component.
