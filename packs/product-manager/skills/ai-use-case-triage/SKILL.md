---
name: ai-use-case-triage
description: Turn a pile of candidate AI use cases into a ranked portfolio — each scored on value, feasibility, and risk with the weights shown, a recommended first slice that can prove or kill the thesis, and an explicit not-yet list with the condition that would promote each entry. Use when a team has more AI ideas than capacity and needs to choose, or asks "where should we actually start with AI". Do NOT use to assess whether the organisation is ready at all (that's ai-readiness-assessment) or to price a single decision (that's business-case).
---

# ai-use-case-triage

Most AI adoption stalls not from lack of ideas but from too many, all sounding equally promising. This produces a **ranked portfolio with rejections**: what to do first, what to hold, and the condition that would move a held item onto the list.

A triage that promotes everything has triaged nothing. The not-yet list is the deliverable's spine.

## How to respond

1. **Inventory the candidates.** From whatever the user brought — a brainstorm, a backlog, interview notes. Each candidate is stated as **a workflow and a person**, not a technology: ✅ "Support agents drafting first-response replies" — ❌ "Use LLMs in support." If a candidate is a technology looking for a job, say so and either recast it or drop it.

2. **Score each on three axes, 1–5, and show the weights.** Default weights: **value 40 · feasibility 35 · risk 25**. State them, and restate them if the user's context justifies different ones (a regulated environment legitimately weights risk higher). Hidden weights make a ranking an opinion.
   - **Value** — time recovered, quality lifted, or revenue/cost moved. Quantify where the input allows; mark `directional` where it doesn't. Never invent a number.
   - **Feasibility** — is the input data reachable, is the output checkable, does the workflow already have a review step? A task whose output nobody can verify is not feasible, however easy the prompt.
   - **Risk** — blast radius if the output is wrong and someone acts on it. Score the *consequence*, not the technology's reputation.

3. **Rank, then sanity-check the top.** The highest score wins only if its **failure is survivable and visible**. A high-value, high-risk item where a wrong answer reaches a customer unreviewed is not a first slice, whatever the arithmetic says — demote it and say why.

4. **Name the first slice, and what it proves.** One use case, with the observable that would confirm or kill the thesis and a time box. ✅ "Draft first-response replies for the top 3 ticket categories; the thesis dies if agents edit more than half the draft body after 4 weeks." A first slice with no kill condition is a pilot that runs forever.

5. **Write the not-yet list with promotion conditions.** Every rejected candidate gets one line saying what would change the answer — "when the knowledge base is deduplicated", "when a human review step exists in the workflow". A rejection with no condition reads as a permanent no and gets re-litigated next quarter.

6. **Hand off.** The first slice's economics → `business-case`; how success will be measured → `success-metrics`; how it reaches people → [`ai-adoption-rollout`](../ai-adoption-rollout/SKILL.md); whether the output can be evaluated at all → `llm-eval-harness`.

## Quality bar

- **The weights are shown and justified in one line.** A ranking with hidden weights is an opinion wearing a table.
- **Every score has a one-line reason.** A bare 4 is not a judgement anyone can challenge.
- **The not-yet list is non-empty**, and every entry carries a promotion condition. If nothing was rejected, the triage didn't happen.
- **Each candidate names a workflow and a person**, not a technology.
- **The first slice has a kill condition** with an observable and a time box.
- **Unknown numbers are marked `directional`**, never invented — a fabricated ROI figure poisons every decision downstream.

## When to use this skill

- ✅ More AI ideas than capacity, and the team needs a defensible order.
- ✅ "Where should we start with AI?" from a leader who has heard a dozen pitches.
- ✅ Re-triaging a stalled portfolio where three pilots are half-running.

## When NOT to use this skill

- ❌ Assessing whether the organisation can adopt anything yet — that's [`ai-readiness-assessment`](../ai-readiness-assessment/SKILL.md).
- ❌ Pricing one option properly (build vs buy, Option 0, cost layers) — that's `business-case`.
- ❌ Planning the human rollout of a chosen use case — that's [`ai-adoption-rollout`](../ai-adoption-rollout/SKILL.md).
- ❌ Writing requirements for the thing you picked — that's `prd-draft`.

## Anti-patterns to avoid

- ❌ **A portfolio with no rejections.** Ranking ten ideas 1–10 and calling it a roadmap is capacity denial, not triage.
- ❌ **Scoring the technology instead of the workflow.** "RAG: 5/5" is not a use case. The unit is a person doing a job.
- ❌ **Invented value numbers.** A confident "$400k/yr saved" with no source is the single fastest way to lose a room that includes a finance lead.
- ❌ **Ignoring verifiability.** Feasibility is not "can a model produce this?" — it is "can someone tell whether it's right, before it matters?"
- ❌ **A first slice that can't fail.** If no observable would kill it, it isn't a pilot; it's a commitment with a pilot's label.

**Non-interactive:** with no user to ask, use the default weights and tag them `[assumption]`. If the input contains no candidate use cases — only a general request to "use AI" — emit `BLOCKED: need at least three candidate workflows to triage` rather than inventing a portfolio.
