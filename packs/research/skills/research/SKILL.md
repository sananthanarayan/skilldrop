---
name: research
description: Take a question that turns on why something happened to an answer the evidence can carry: a plan tied to the decision it serves, a synthesis of the sources with every claim cited, and rival explanations ranked by how little evidence contradicts them, with a gate that sends the work back for the observation that would tell the leaders apart. Use when the user says "research why…", "find out what's causing…", "run the research loop", or needs a decision-ready answer on which explanation the evidence supports.
---

# research

One question, from scoping to an answer someone can decide on. The three skills each work
alone; in order, each one constrains the next. The plan fixes what would change the decision
before anyone reads a source, so the findings can't be read to fit. The synthesis cites every
claim, so the comparison rates only evidence that exists. The gate then asks whether that
evidence separates the explanations, which none of the three can judge about its own output.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `plan` | generate | [`research-plan`](../../skills/research-plan/SKILL.md) | — |
| 2 | `synthesise` | generate | [`source-synthesis`](../../skills/source-synthesis/SKILL.md) | — |
| 3 | `compare` | verify | [`hypothesis-comparison`](../../skills/hypothesis-comparison/SKILL.md) | **G7** review |

## How to run this loop

1. **Plan before reading.** Run `research-plan` on the question. It asks what decision the
   research serves, who makes it and by when; don't skip that. Save the plan as `plan.md`.
   Carry three things from it into every later stage: the decision, the findings that would
   change it, and the stopping rule.
2. **Gather the sources the plan names.** The person supplies them, or you collect them under
   the plan's inclusion and exclusion criteria with the search strings it wrote. A source the
   criteria exclude stays out, however convenient. List each as `S1: …` in `sources.md`.
3. **Synthesise, cited.** Run `source-synthesis` in its cited form (an evidence summary with
   `[S1:p4]` citations), on the plan's question. It counts a source that repeats another once,
   and its citation check runs before you hand anything on. Save it as `synthesis.md`.
4. **Compare the explanations.** Run `hypothesis-comparison` with the observation from the
   plan as the thing to explain and the synthesis's findings as the evidence, keeping their
   citations. Every evidence row cites a source from `sources.md` or is marked
   `[assumption]`. The comparison names the leader, the diagnostic evidence, the linchpins and
   the next observation that would tell the top two apart.
5. **Judge the evidence at G7.** Ask four questions, then choose the verdict below:
   - Does at least one diagnostic row separate the leader from the runner-up?
   - Does any linchpin rest on a single source or an `[assumption]`?
   - Is the plan's stopping rule met?
   - Would the finding move the decision past a threshold the plan set?
6. **On `REVISE`, get the observation, not more of the same.** Return to `synthesise` with the
   one observation the comparison named as discriminating. Add it to `sources.md` as a new
   source, re-synthesise, and compare again. More sources that the top two both predict
   equally add nothing. Each return counts against the cap. When only a person can get the
   observation (a data pull, an interview, a log nobody gave you), stop here: say what to
   get, from whom, and what each result would mean, and resume when they add it.
7. **Hand over the answer, then the verdict.** Lead with the explanation the evidence favours
   and its confidence, then what that means for the decision named in the plan, then the
   open conditions. The matrix and the synthesis go underneath, for anyone who wants to
   check. Close with the gate on its own line, `G7: <VERDICT>`, and one sentence of reasons.
   The skills keep their own terms out of a reply; the loop's verdict is the exception,
   because the run log and the next round both read it.

## Verdicts

Defined in [`contracts/terminals.json`](../../../../contracts/terminals.json). G7 emits:

- `PROCEED`: diagnostic evidence separates the leader, no linchpin rests on one source or an
  assumption, and the stopping rule is met.
- `PROCEED WITH CONDITIONS`: the leader is clear, but a named linchpin is unchecked or a
  sub-question is still open. The conditions travel with the answer: each one says what to
  check and how the decision changes if it comes out the other way.
- `REVISE`: the top two are not separated by any diagnostic row, or the leader rests on one
  weak row. Return to `synthesise` with the discriminating observation.
- `RECONSIDER`: every hypothesis is contradicted by strong evidence, or the observation
  itself turned out wrong (a tracking change, a definition change). The question needs
  re-planning, so the loop ends here and a new run starts at `plan`.
- `BLOCKED`: no decision to serve, no observation to explain, or no sources.

On the cap-th `REVISE`, emit `PROCEED WITH CONDITIONS` with the leaders still tied and say
plainly that the evidence doesn't settle it: the decision will be made under that
uncertainty, and the discriminating observation is the first thing to get.

## Non-interactive runs

With no person to name the decision, `research-plan` either infers it as an `[assumption]` or
emits `BLOCKED: need the decision this research informs, who makes it, and by when`. Carry
that `BLOCKED` through as the loop's verdict. Run no further stages on an invented decision:
a stopping rule set against a guessed decision stops at the wrong place. With no sources and
nothing to collect them from, emit `BLOCKED: need the sources, or access to collect them
under the plan's criteria`.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and record that it ran degraded. A degraded `compare` still builds a matrix that
ranks by inconsistency and names its linchpins, because G7 can't be judged without them.
Never skip G7.

## Run log (opt-in)

Only when the environment variable `SKILLDROP_LOOP_LOG` is set to a file path: after each
gate's verdict, append one JSON line to that file. Nothing else is recorded, and nothing is
sent anywhere. When the variable isn't set, or you can't read it, skip this section.

```bash
printf '%s\n' '{"ts":"2026-10-19T14:03:00Z","loop":"research","stage":"compare","gate":"G7","verdict":"REVISE","round":1}' >> "$SKILLDROP_LOOP_LOG"
```

Fields: `ts` (UTC), `loop`, `stage`, `gate` (`null` for a stage without one), `verdict` (the
gate's exact word), and `round` (1 for the first attempt, counting returns under the cap).
The log holds verdicts only: never the question, the sources or the findings.
`skilldrop loop-stats` summarises the file.

## Quality bar

- **What would change the decision is written before any source is read.** Thresholds set after the findings are read get set to fit them.
- **Every evidence row in the matrix cites a source in `sources.md` or is marked `[assumption]`.** A matrix of uncited evidence ranks a favourite theory.
- **G7 is judged on diagnostic evidence.** Rows that every hypothesis predicts equally are named and set aside, however many there are.
- **A `REVISE` brings back the one observation that discriminates.** It does not bring back more sources of the same kind.
- **The answer leads with the explanation and what it means for the decision.** The matrix is the working, not the reply.

## Anti-patterns to avoid

- ❌ **Synthesising before the plan exists.** The sources then decide the question, and the stopping rule is whenever the reading runs out.
- ❌ **Rating evidence the synthesis didn't cite.** An observation from memory or a plausible industry figure is an `[assumption]` row, weighted as one.
- ❌ **Counting a press release and the three articles that quote it as four sources.** The synthesis counts them once, and so does the matrix.
- ❌ **Passing G7 on volume.** Ten consistent rows that every rival also explains don't separate anything.
- ❌ **Looping past the cap in search of certainty.** At the cap, say that the evidence doesn't settle it and name the next check.
- ❌ **Re-planning inside the loop after `RECONSIDER`.** A new question is a new run, with its own plan and stopping rule.
