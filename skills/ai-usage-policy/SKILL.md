---
name: ai-usage-policy
description: Draft an organisation's AI acceptable-use policy — three data-sensitivity tiers with what may be put into a tool at each, permitted and prohibited uses stated as behaviours, a human-review matrix keyed to consequence, an approved-tool list with an exception route, and a named owner per rule. Use when a team needs rules for what people may put into AI tools, or asks for an AI acceptable-use or governance policy. Do NOT use to write a repo's agent-tooling policy (that's agents-md-generator) or to analyse one agent's capability surface (that's agent-threat-model).
---

# ai-usage-policy

Write the policy people will actually follow: **what may go in, what must be checked before it goes out, and who to ask when the rule doesn't fit.** The audience is every employee, not the security team — so it reads as rules for a job, not controls for an auditor.

A policy that prohibits without offering a permitted path doesn't reduce risk; it moves the same work onto personal accounts where nobody can see it. Every prohibition here carries an alternative.

## How to respond

1. **Establish scope and the regulatory floor.** Which population, which tools, and any regime already binding (sector rules, customer contracts, an existing data-classification scheme). If the organisation already classifies data, **reuse those tier names** rather than inventing a parallel scheme — two classification systems means neither is followed. Cap clarifying questions at 2.

2. **Define three data tiers and what may enter a tool at each.** Three, because five is not memorable and one is not a policy:

   | Tier | Examples | Rule |
   |---|---|---|
   | **Open** | public docs, published marketing, open-source code | any approved tool |
   | **Internal** | internal docs, non-personal telemetry, private repo code | approved tools with data-retention off / enterprise terms |
   | **Restricted** | personal data, credentials, customer content under contract, regulated records | never pasted; only via a named reviewed integration, if at all |

   Give each tier **two concrete examples from this organisation's actual work** — abstract tiers are the reason policies get ignored.

3. **State permitted and prohibited uses as behaviours.** ✅ "Drafting a first version of a customer email, then editing before sending." ❌ "Inappropriate use." Every prohibition names the **permitted alternative**: "Do not paste customer records to summarise them — use the approved integration, which does the same thing without the data leaving."

4. **Build the human-review matrix on consequence, not on technology.** What must a human check before an AI-assisted output is acted on? Key it to blast radius: reaches a customer · commits money or a legal position · changes production · informs a personnel decision. Each row says who reviews and what "reviewed" means. Low-consequence internal drafting needs no gate — say so, or the policy loses credibility everywhere else.

5. **List approved tools, and give an exception route.** Named tools with the tier they're cleared to. Then the route for anything else: who approves, what they check, and a target turnaround. **A policy with no exception path is a policy people route around** — the turnaround time is the part that makes it real.

6. **Name an owner per section, a review date, and the disclosure rule.** Owners as roles. A review date, because tool terms change. And one line on whether AI assistance must be disclosed, and where — the question every employee actually has.

## Quality bar

- **Every rule has a named owner role** and the document has a review date. An unowned policy is a document, not a control.
- **Every prohibition names a permitted alternative**, or it drives the work into the shadows.
- **Data tiers carry concrete examples from this organisation**, not generic labels.
- **The review matrix is keyed to consequence, not to tool or model.** Model names age out in months; consequences don't.
- **There is an exception route with a turnaround time.**
- **Written for the whole staff.** If a non-technical reader hits an unexplained term, rewrite it — the audience is everyone, and unread rules govern nothing.
- **No invented regulation.** Cite only regimes the user named; where applicability is unclear, mark `[confirm with counsel]` rather than asserting a legal position.

## When to use this skill

- ✅ "What are people allowed to put into these tools?" — the question every rollout hits in week one.
- ✅ Standing up governance before or alongside an AI rollout.
- ✅ Replacing an informal "be sensible" norm with something reviewable.

## When NOT to use this skill

- ❌ Writing a repository's agent-tooling policy (`AGENTS.md` — build commands, conventions, what agents may edit) — that's `agents-md-generator`.
- ❌ Threat-modelling one agent's data reach and exfiltration paths — that's `agent-threat-model`.
- ❌ Planning how the tool reaches people — that's [`ai-adoption-rollout`](../ai-adoption-rollout/SKILL.md).
- ❌ Assessing whether governance is mature enough yet — that's [`ai-readiness-assessment`](../ai-readiness-assessment/SKILL.md).
- ❌ A security review of a design — that's `threat-model`.

## Anti-patterns to avoid

- ❌ **Prohibition without an alternative.** "Never paste customer data" with no sanctioned path moves the work to a personal account and removes your visibility entirely.
- ❌ **Naming models and versions in the rules.** They change quarterly; consequence-based rules survive. Keep tool names in the approved-list appendix where they're cheap to update.
- ❌ **Five or more tiers.** Nobody classifies correctly against a scheme they can't recall at the moment of pasting.
- ❌ **Writing for auditors.** A policy in control language gets filed, not followed. Plain rules for a working day.
- ❌ **No exception route.** Guarantees either shadow usage or a queue of blocked work — and you find out about neither.
- ❌ **Requiring review of everything.** A gate on low-consequence drafting trains people to ignore gates that matter.

**Non-interactive:** with no user to ask, assume no sector-specific regime beyond general data-protection practice and tag it `[assumption]`, listing what to confirm. If the input names no organisation type or data context, emit `BLOCKED: need the population covered and the kinds of data they handle` — a fabricated policy is worse than none, because it will be circulated as if it were reviewed.
