---
name: ai-usage-policy
description: Draft an organisation's AI use policy or staff guidance from what it has told you about its people, tools, data and worries — every "don't" paired with what to do instead (or who decides, when no approved way exists yet), what to do if data has already gone into a tool, and no claim about a tool, licence, owner, regulation or commitment the input didn't give. Written in the length, labels and voice the audience needs. Use when a team needs rules for what people may put into AI tools, or asks for an AI acceptable-use or governance policy. Do NOT use to write a repo's agent-tooling policy (that's agents-md-generator) or to analyse one agent's capability surface (that's agent-threat-model).
---

# ai-usage-policy

**The rule: every "don't" comes with what to do instead.** A policy that only forbids doesn't
stop the work; it moves it to a personal account where nobody can see it. So each prohibition
names the approved way to do the same task today: ✅ *"Don't paste client reports into a chat
tool to summarise them. Use the summariser in the document system, which keeps them inside."*
When no approved way exists yet, the policy says so and says who decides: ✅ *"There's no
approved tool for transcribing interviews yet. Ask the operations lead before using one."*

The policy also says **what to do if it has already happened**: data pasted into the wrong
tool, a draft sent unchecked. Who to tell, how fast, and that telling is what's expected.

A second rule sits beside it: **claim nothing you weren't given.** No statement about where a
tool sends data, whether it trains on inputs, how many seats exist, who owns the policy, how
fast exceptions are handled, or which law applies, unless the input says so. A vendor's own
data-sheet is the vendor's claim: report it as "the vendor says", never as fact, and never
let it be the reason sensitive data is allowed. Check the tools against what you were told
(seat counts against headcount, a contract that has lapsed, terms not yet signed) and say
where they don't line up.

## How to respond

1. **Write for the people who'll read it, at the size asked for.** "A short note for our
   twelve staff", "one page to attach for a client", "the full policy for the board": that
   sets the length, voice and structure. Use the organisation's own words for its data and
   roles; if it already classifies data, use those names, not a new scheme.

2. **Say what's allowed, plainly, first.** The common, low-risk uses (drafting, rewording,
   brainstorming on non-sensitive material) are named as fine, so the restrictions read as
   targeted rather than blanket.

3. **The restrictions, each with its alternative.** State them as behaviours tied to the
   organisation's real data: what not to put in which tool, and what to do instead. Review
   before use only where the consequence warrants it: something reaching a customer, money,
   a legal position, a decision about a person.

4. **The tools, as far as you know them.** The tools the input names, and what each is
   cleared for, as far as the input says. For anything else, the route to ask, with the role
   who decides if the input names one, or "to be agreed" if it doesn't.

5. **If something has already gone wrong.** One short section: who to tell, and that
   reporting quickly is what's expected.

6. **Keep notes to the requester out of the policy.** The policy is a document someone will
   circulate. Questions for the person who asked (who owns this, which tool contract to
   check, whether a law applies) go in a short list after it, never as bracketed tags inside.

7. **Deliver from what you have.** With anything about the organisation to go on, write the
   policy and state any assumption in one line. Ask first only when you don't know who it is
   for or what kind of data they handle.

## Quality bar

- **Every prohibition names an alternative,** or says no approved way exists yet and who
  decides.
- **There is a line on what to do if it has already happened.**
- **Nothing unsupplied:** no data-handling claim, seat count, owner, turnaround, commitment or
  regulation the input didn't give; vendor claims are attributed to the vendor.
- **The tool list is checked against the input** and mismatches are named.
- **The length, voice and labels fit the audience asked for.**
- **No notes, tags or questions to the requester inside the policy.**

## When to use this skill

- ✅ "What are people allowed to put into these tools?" — the question every rollout hits in week one.
- ✅ Standing up guidance before or alongside an AI rollout.
- ✅ Replacing an informal "be sensible" norm with something people can follow.

## When NOT to use this skill

- ❌ Writing a repository's agent-tooling policy (`AGENTS.md` — build commands, conventions, what agents may edit) — that's `agents-md-generator`.
- ❌ Threat-modelling one agent's data reach and exfiltration paths — that's `agent-threat-model`.
- ❌ Planning how the tool reaches people — that's [`ai-adoption-rollout`](../ai-adoption-rollout/SKILL.md).
- ❌ Assessing whether governance is mature enough yet — that's [`ai-readiness-assessment`](../ai-readiness-assessment/SKILL.md).
- ❌ A security review of a design — that's `threat-model`.

## Anti-patterns to avoid

- ❌ **Prohibition without an alternative.** It moves the work out of sight.
- ❌ **Repeating the vendor.** "The tool never stores your data" because a sales sheet said so.
- ❌ **Invented machinery.** An owner, a five-day exception turnaround, a quarterly review, a
  tier scheme the organisation never asked for.
- ❌ **The full framework on a short note.** Tier tables and review matrices for a twelve-person
  team that asked for half a page.
- ❌ **Bracketed notes in the policy.** `[confirm with counsel]` in a document about to be
  attached for a client.
- ❌ **Naming laws the user didn't name.** Say what to check, in the note after the policy.
- ❌ **Requiring review of everything.** A gate on low-risk drafting trains people to ignore the
  gates that matter.
