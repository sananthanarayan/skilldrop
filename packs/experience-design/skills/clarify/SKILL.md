---
name: clarify
description: Take a service people struggle with from its page to the service behind it: a content spec and plain-language rewrite from what users need, every string on the form or flow, and a service blueprint that tests whether those fixes reach the fail points behind the complaints, with a gate that sends the work back to the page when it misses a fail point and out to product when the fix is backstage. Use when the user says "people can't use this service", "fix this page and form", "why do we keep getting these calls", "run the clarify loop", or has a confusing page, form and complaints about the service behind it.
---

# clarify

One service, from the words people read to the work behind them. A clearer page stops the calls
that come from confusion and none of the calls that come from a wait or a lost handoff. The
content spec and the strings fix the words. Then the blueprint traces each complaint to the cell
that causes it. That shows which complaints the new words reach and which need the service
itself to change. Neither writing skill can judge that about its own output.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `page` | generate | [`content-design`](../../skills/content-design/SKILL.md) | — |
| 2 | `strings` | generate | [`ux-writing`](../../skills/ux-writing/SKILL.md) | — |
| 3 | `blueprint` | verify | [`service-blueprint`](../../skills/service-blueprint/SKILL.md) | **G14** review |

## How to run this loop

1. **List the complaints first.** From the calls, tickets, survey answers or anything else the
   person brought, write `complaints.md`: each kind of complaint, how often if known, and one
   quote. Every later stage reads it. Without complaints, the loop checks the words against
   nothing.
2. **Write the page.** Run `content-design` on the current page, with the complaints as
   evidence of what users need to know. The questions the page must answer come from the
   complaints first. Save the spec and rewrite as `page.md`, with the readability before and
   after.
3. **Write the strings.** Run `ux-writing` on the form or flow, using the terms the content spec
   chose, so the page and the form call the same thing by the same name. Save the string table
   as `strings.md`.
4. **Blueprint the service.** Run `service-blueprint` on the scenario the complaints describe,
   from the page through to the outcome the person is waiting for. Trace every complaint in
   `complaints.md` to the cell that causes it. Then mark each complaint as reached by the page,
   reached by the strings, or caused backstage. Save it as `blueprint.md`.
5. **Judge the fixes at G14.** Ask three questions, then choose the verdict below:
   - Is every complaint caused by the words reached by a specific line in `page.md` or
     `strings.md`?
   - Which complaints are caused backstage, and does the page at least tell people what
     happens and how long it takes?
   - Do the page, the strings and the blueprint use the same names for the same things?
6. **On `REVISE`, fix the words for the missed complaint.** Return to `page` with the complaint
   and the cell that causes it. Then re-run `strings` when the change touches the form. Each
   return counts against the cap.
7. **Hand over what changes and what can't change here.** Lead with the complaints the new page
   and form should stop, and the ones they can't, with the backstage fix and its owner. The
   page, the strings and the blueprint go underneath.

## What the reply says

- **Lead with what was asked for, in plain words:** the complaints the new page and form should stop, the ones they can't, and the backstage fix and its owner for each of those.
- **No loop internals.** No gate id, verdict word, stage or skill name, and no path inside a
  skill folder, in the reply or in any file the person receives. Say the outcome instead:
  ✅ *"The new page should stop the 'which documents count' calls. 'Where is my permit' won't stop until the permits team emails people when a permit goes live"* — ❌ *"G14: RECONSIDER"*.
- **The verdict goes to the run log only,** when one is set. The reply never mentions the run
  log, whether it is set, or how the run was set up.
- **A person's decision never holds back the work.** Deliver everything up to it, then name
  the decision in one line: who makes it, and what each answer means. When the request
  already holds their decision ("the permits team has agreed to send the email"), record it as theirs and carry on.
- **Stop only when nothing can be made.** With an essential input missing, the first line says
  in plain words what's missing, then what you'll produce once it arrives.

## Verdicts

Defined in [`contracts/terminals.json`](../../../../contracts/terminals.json). G14 emits:

- `PROCEED`: every complaint caused by the words is reached by a named line, the names match
  across all three, and no complaint is caused backstage.
- `PROCEED WITH CONDITIONS`: the words are right, but some complaints are caused backstage.
  The page says what happens and how long it takes, and each backstage fix travels with its
  owner as a condition.
- `REVISE`: a complaint caused by the words is reached by no line, or the page and form name
  the same thing differently. Return to `page`.
- `RECONSIDER`: most of the complaints are caused backstage, so new words won't move them. The
  fix is a change to the service, so the work goes to product as a requirement, with the
  blueprint's ranked fixes, and the loop ends here.
- `BLOCKED`: no service or scenario can be identified, or there is no current page or form.

On the cap-th `REVISE`, emit `PROCEED WITH CONDITIONS` with the missed complaint named as open.

## Non-interactive runs

A missing reader or voice degrades to the skills' `[assumption]` lines. With no complaints at
all, tag the loop's output `[no complaint evidence]` and judge G14 on the blueprint's fail
points alone. With no service or scenario, `service-blueprint` emits
`BLOCKED: need the service and one customer scenario`; carry it through as the verdict.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and record that it ran degraded. A degraded `blueprint` still traces every complaint to
a frontstage, backstage or support cause, because G14 can't be judged without that trace.
Never skip G14.

## Run log (opt-in)

Only when the environment variable `SKILLDROP_LOOP_LOG` is set to a file path: after each
gate's verdict, append one JSON line to that file. Nothing else is recorded, and nothing is
sent anywhere. When the variable isn't set, or you can't read it, skip this section.
The reply never mentions the run log, whether or not it is set.

```bash
printf '%s\n' '{"ts":"2026-11-03T10:15:00Z","loop":"clarify","stage":"blueprint","gate":"G14","verdict":"REVISE","round":1}' >> "$SKILLDROP_LOOP_LOG"
```

Fields: `ts` (UTC), `loop`, `stage`, `gate` (`null` for a stage without one), `verdict` (the
gate's exact word), and `round` (1 for the first attempt, counting returns under the cap).
The log holds verdicts only: never the page, the complaints or the quotes.
`skilldrop loop-stats` summarises the file.

## Quality bar

- **The complaints are written down before any rewrite.** Every later stage is judged against them.
- **Every complaint is traced to the cell that causes it,** and marked as reached by the page, reached by the strings, or caused backstage.
- **The page and the form use the same name for the same thing,** and the blueprint uses it too.
- **A backstage cause is named with its owner,** never written around with friendlier words.
- **The reply says which complaints the new words can't stop.**

## Anti-patterns to avoid

- ❌ **Rewriting the page from a style guide instead of the complaints.** The page reads better and the same calls keep coming.
- ❌ **Fixing a wait with reassuring copy.** "We're working on it" doesn't shorten a five-week wait; say how long it takes, and send the wait to its owner.
- ❌ **Writing the strings before the page.** The form then names things one way and the page another.
- ❌ **Passing G14 because readability improved.** A lower grade level is not a complaint reached.
- ❌ **Treating `RECONSIDER` as failure.** Finding that the service, not the page, causes the calls is the result.
- ❌ **Gate talk in the reply.** "G9: READY, G9.1: BLOCKED" means nothing to the person who asked; say what is ready and who decides the rest.
