---
name: design
description: Take a ratified requirement to a recorded architectural decision — constraints, structure, diagrams, threats, then a panel that must agree before the decision is written down. Use when the user is designing a system, choosing an architecture, or asking how something should be built.
---

# design

The loop with the worst reversibility profile in the repo. A discovery mistake costs a
re-brief; a design mistake surfaces months later, in code nobody wants to unwind. That is why
its gate is a **panel** — independent positions, surfaced cruxes, recorded dissent — and not
a script, and why the decision is recorded only *after* the panel agrees.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `constrain` | generate | [`context-graph`](../../../core/skills/context-graph/SKILL.md), [`nfr-spec`](../../skills/nfr-spec/SKILL.md) | — |
| 2 | `shape` | generate | [`design-doc`](../../skills/design-doc/SKILL.md), [`architecture-diagrams`](../../skills/architecture-diagrams/SKILL.md) | — |
| 3 | `threat` | verify | [`threat-model`](../../skills/threat-model/SKILL.md) | — |
| 4 | `ratify` | gate | [`council-review`](../../../core/skills/council-review/SKILL.md) | **G1** review |
| 5 | `record` | generate | [`adr-generator`](../../skills/adr-generator/SKILL.md), [`context-graph`](../../../core/skills/context-graph/SKILL.md) | — |

## How to run this loop

1. **Constrain before shaping.** First run `context-graph` where the design will land. List the
   decisions already in force there, each by id, and any the code has drifted from. A new
   design either keeps each one or says which it supersedes; when the repo has no records,
   say so. Then run `nfr-spec`, always. A design produced before its quality targets exist
   gets judged on taste, and taste does not survive a review panel.
2. **Shape prose and picture together.** `design-doc` and `architecture-diagrams` are one
   artifact in two renderings. A diagram that disagrees with the doc is a defect in both.
3. **Attack it before ratifying.** `threat-model` consumes the design directly. Running it
   after G1 means the panel ratified something nobody had attacked.
4. **Ratify at G1.** `council-review` takes positions *before* cross-talk, names the cruxes,
   and records what would change each position. `REVISE` returns to `shape`. `SPLIT` and
   `RECONSIDER` leave the loop. What comes out is a set of trade-offs and open risks; the
   people who decide read those, not the positions or who held them.
5. **Read the house rules before writing or touching a record.** Find the repository's ADR
   README, template or the record that defines how decisions are written. Follow its format,
   its sections and its rules for changing old records. When it has none, use
   `adr-generator`'s format.
6. **Record last, and record the decision as it was made.** `adr-generator` writes the
   decision *after* it is a decision, with the rejected options and the reasoning that killed
   them. An ADR written before G1 is a proposal wearing an ADR's clothes. When the request
   already holds the decision ("the CTO chose Kafka"), the ADR records the decider's choice in
   their terms, as theirs. The risks, threats and gaps the work found go in the ADR too, where
   the house format puts consequences (Consequences, Risks, Open issues). Each is marked open
   and not accepted by the decider, never written as their condition, fallback or acceptance.
   When nobody has decided yet, the ADR's status is `Proposed` and names who decides.
7. **Close the supersessions the house rules allow.** Run `context-graph` again. Every record
   the new ADR replaces gets only the change the house rules permit on an accepted record,
   such as a "Superseded by" line; nothing else in it is edited. When the new decision replaces
   only part of an older one, say exactly which part on both sides, and don't mark the whole
   record superseded while the rest still governs. The new ADR names the code it governs. A
   supersession recorded on one side only is the most common way a decision log starts to lie.
8. **Deliver what was asked for, in the form asked for.** When the person names the
   deliverables ("a design doc and an ADR"), the quality targets, threat model and diagrams go
   inside those files, as sections, instead of as extra files nobody asked for. When they
   don't name them, write the design doc and the ADR.
9. **Name only files that exist.** Write each file into the working folder before the reply
   names it, and list them by the paths they were written to. A design, diagram or ADR you
   describe but didn't write is not named as a file.

## What the reply says

- **Lead with the person's decision or question, in plain words:** what was decided (or the
  answer to what they asked) and why. When recording a decision already made, the first lines
  say the record is written and name the single most important risk it carries, in plain
  words. Then the other risks, the quality targets, the design and the diagrams.
- **No loop internals.** No gate id, verdict word, stage or skill name, and no path inside a
  skill folder, in the reply or in any file the person receives. Say the outcome instead:
  ✅ *"Use event sourcing for orders. The open trade-off is running cost: replaying 40 million events takes about two hours, so a snapshot store is worth adding before year two"* — ❌ *"G1: PROCEED"*.
- **No narrated panel.** Present the review as trade-offs and open risks. Never name
  reviewers, personas or seats, and never write "dissent", "the panel overruled" or a note
  that no panel ran.
- **A decision already made is recorded as the decider made it.** The ADR holds their choice
  in their terms, and lists the risks you found as open, not accepted. The reply puts the same
  risks in front of the decider. None is written as a condition, fallback or acceptance they
  didn't give.
- **Say which records changed and how,** in one line each: the new ADR, and the line added to
  any record it supersedes, in whole or in part.
- **Name only files that exist in the working folder,** by the paths they were written to.
- **The verdict goes to the run log only,** when one is set. The reply never mentions the run
  log, whether it is set, or how the run was set up.
- **A person's decision never holds back the work.** Deliver everything up to it, then name
  the decision in one line: who makes it, and what each answer means. When the request
  already holds their decision ("the architecture lead has already chosen Postgres"), record it as theirs and carry on.
- **Stop only when nothing can be made.** With an essential input missing, the first line says
  in plain words what's missing, then what you'll produce once it arrives.

## Verdicts

Defined in [`contracts/terminals.json`](../../../../contracts/terminals.json). `PROCEED WITH
CONDITIONS` is the common outcome and the most abused: the conditions are part of the
decision. When a person ratified it, `record` carries their conditions into the ADR. When the
loop ratified it, the conditions go to the decider as open risks and the ADR stays `Proposed`
until they accept them.

## Non-interactive runs

`council-review` can be run by the agent itself, so G1 is satisfiable without a human. The
reply never says how the review was run; it gives the trade-offs and risks it found. `SPLIT` is
not satisfiable alone — a genuine unresolved split needs a person. Deliver the design and both
options with what each costs, and name the decision and who makes it, in plain words.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version, and record
the stage as degraded in the run log, not the reply. If `council-review` is missing, do not
skip G1 — review the design inline against its own quality attributes.

## Run log (opt-in)

Only when the environment variable `SKILLDROP_LOOP_LOG` is set to a file path: after each
gate's verdict, append one JSON line to that file. Nothing else is recorded, and nothing is
sent anywhere. When the variable isn't set, or you can't read it, skip this section.
The reply never mentions the run log, whether or not it is set.

```bash
printf '%s\n' '{"ts":"2026-10-01T14:03:00Z","loop":"design","stage":"ratify","gate":"G1","verdict":"PROCEED","round":1}' >> "$SKILLDROP_LOOP_LOG"
```

Fields: `ts` (UTC), `loop`, `stage`, `gate` (`null` for a stage without one), `verdict` (the
gate's exact word), and `round` (1 for the first attempt, counting returns under the cap).
`skilldrop loop-stats` summarises the file: which gates pass first time, which loop back, and
which end in `BLOCKED`.

## Quality bar

- **Quality targets exist before structure does.** `nfr-spec` is stage 1 because a design without numbers can only be argued about.
- **The ADR names what was rejected and why.** A decision record with one option is a description of what happened, not a decision.
- **Disagreement is kept, not resolved away.** It reaches the person as a trade-off with what each side costs; a review that always agrees isn't testing anything.
- **The ADR's decision is the decider's.** Every condition in it traces to them. Every risk the loop found is in it too, marked open and not accepted, and in the reply.
- **Existing records change only as the house rules allow.** A partial supersession names the part replaced, and the record isn't marked wholly superseded.
- **The deliverables are the ones asked for.** Quality targets, threats and diagrams sit inside them as sections.
- **Every file the reply names exists** in the working folder at the path given.
- **The reply leads with the person's decision or question,** before threats, NFRs and diagrams.
- **The diagram and the doc say the same thing.** They are checked against each other before G1, not after someone builds from the wrong one.
- **The design names the decisions already in force where it lands,** and which of them it keeps or supersedes.
- **After `record`, the records agree with each other:** each record the new ADR supersedes, wholly or in part, says so too.

## Anti-patterns to avoid

- ❌ **Writing the ADR before G1.** It pre-commits the panel to a decision it has not made, and every reviewer can feel it.
- ❌ **Running `threat-model` after ratification.** The panel then ratified an unattacked design, which is the failure this ordering exists to prevent.
- ❌ **Treating `PROCEED WITH CONDITIONS` as `PROCEED`.** The conditions must reach the decider, and the ADR once they accept them; dropping them is how a conditional approval silently becomes unconditional.
- ❌ **Designing over a decision nobody read.** A new design that quietly contradicts a current ADR leaves two decisions in force on one system, and the next reader can't tell which one wins.
- ❌ **Skipping `constrain` because the NFRs are "obvious".** Obvious targets are the ones nobody writes down and everybody remembers differently.
- ❌ **Writing your conditions into their decision.** "Accepted, provided a fallback to Postgres" when the decider said only "use Kafka" puts words in their record. List the missing fallback as an open risk instead.
- ❌ **Leaving the risks out of the record.** An ADR that is silent on a risk the work found reads as if the decider accepted it, and the reply that named it is gone by next quarter. Record it as open.
- ❌ **Editing an accepted record beyond what the house rules allow,** or marking a whole record superseded when only part of it is replaced. The next reader loses the part that still governs.
- ❌ **Adding files nobody asked for.** A separate threat model and NFR file beside the two documents requested scatters the decision; fold them in.
- ❌ **Narrating the panel.** "The security reviewer dissented" or "I didn't run the separate panel" describes the process, not the design; give the trade-off.
- ❌ **Naming a file you didn't write.** "See `docs/adr/0012.md`" when it isn't there sends the reader to nothing.
- ❌ **Leading with the threat model.** The person asked about a decision; answer it first.
- ❌ **Gate talk in the reply.** "G9: READY, G9.1: BLOCKED" means nothing to the person who asked; say what is ready and who decides the rest.
