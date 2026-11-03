---
name: ship-agent
description: Take an AI agent from an idea to a launch a person signed: the loop spec with its exit criteria and cap, the spend caps per stage, a threat model where every lethal-trifecta path has an architectural fix, an eval harness with its pass bar set before the first run, and a review of the real agent configuration before launch, with a gate that sends the design back when a path to exfiltration stays open. Use when the user says "we're building an agent", "design and ship this agent safely", "run the ship-agent loop", or wants an agent taken from design to launch with its risks and evals settled.
---

# ship-agent

One agent, from a described job to a launch its owner signed. Each skill works alone; in order,
each one reads the last one's output. The loop design names every stage and tool, so the budget
caps real stages and the threat model inventories real capabilities. The threat model's attacks
become the eval harness's adversarial cases. The launch review reads the configuration the team
actually built against the capabilities the threat model allowed, which no design document can
check about itself.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `design` | generate | [`agent-loop-design`](../../skills/agent-loop-design/SKILL.md), [`subagent-design`](../../skills/subagent-design/SKILL.md) | — |
| 2 | `budget` | generate | [`agent-budget`](../../skills/agent-budget/SKILL.md) | — |
| 3 | `threat` | verify | [`agent-threat-model`](../../skills/agent-threat-model/SKILL.md) | **G12** review |
| 4 | `evals` | generate | [`llm-eval-harness`](../../skills/llm-eval-harness/SKILL.md) | — |
| 5 | `launch` | gate | [`agent-config-review`](../../skills/agent-config-review/SKILL.md) | **G12.1** human |

## How to run this loop

1. **Design the loop.** Run `agent-loop-design` on the job. Run `subagent-design` after it only
   when the job fans out across agents; a single agent skips it. Save the spec as `design.md`.
   Carry two things into every later stage: the tool and data list, and the done-condition.
2. **Cap the spend.** Run `agent-budget` on the design's stages. Each stage gets a tier, a token
   cap and an abort rule; a stage the design doesn't have gets no budget. Save it as
   `budget.md`.
3. **Threat-model the design.** Run `agent-threat-model` with the design's tool and data list
   as the capability inventory. A capability the design implies but doesn't list is modelled at
   its widest plausible scope and tagged `[assumption]`. Save it as `threat.md`.
4. **Judge the design at G12.** Ask three questions, then choose the verdict below:
   - Does every 🟥 path (private data, untrusted content and a way out, in one context) have an
     architectural fix, not a prompt instruction?
   - Does any fix contradict the design, such as a tool removed that a stage needs?
   - Is every residual risk owned by a named role?
5. **On `REVISE`, change the design.** Return to `design` with the open path and its fix: split
   the context, drop the tool, or put a human gate on the outbound step. Re-run `budget` and
   `threat` on the new design. Each return counts against the cap.
6. **Design the evals.** Run `llm-eval-harness` with the design's done-condition as the task.
   Every attack in the threat model's sweeps becomes an adversarial case in the critical
   subset, which must stay at 100%. The pass bar and regression gate are fixed now. Save it as
   `evals.md`.
7. **Stop while the team builds.** The loop has produced the design, budget, threat model and
   eval plan. Hand them over and stop until the team has a built agent, its configuration
   files and one eval run. Resume at `launch` when they bring them.
8. **Review the launch at G12.1.** Run `agent-config-review` on the real configuration, then
   check each granted capability against `threat.md`: a grant the threat model did not allow
   is a finding, however harmless it looks. Put the review verdict, the eval result against
   the pass bar, and every residual risk in front of the agent's owner. Only they choose the
   verdict. In a non-interactive run, stop and write the decision they face.
9. **Hand over the decision, then the working.** Lead with what the agent will be able to do,
   what it can't, and what still stands between it and launch. The documents go underneath.
   Close with each gate on its own line, `G12: <VERDICT>` and `G12.1: <VERDICT>` (or
   `G12.1: awaiting <role>`), and one sentence of reasons.

## Verdicts

Defined in [`contracts/terminals.json`](../../../../contracts/terminals.json). G12 emits:

- `PROCEED`: every 🟥 path has an architectural fix, no fix contradicts the design, and every
  residual risk has an owner role.
- `PROCEED WITH CONDITIONS`: the fixes are designed but one depends on something unverified,
  such as a sandbox's egress rule. The condition goes into the eval plan as a case and into the
  launch review as a check.
- `REVISE`: a 🟥 path is left open, or its only fix is a prompt instruction. Return to
  `design`.
- `RECONSIDER`: the job can't be done without all three legs of the trifecta in one context,
  such as an agent that must read untrusted email and send email on its own. The job needs a
  person in the loop or a different scope, so the loop ends here.
- `BLOCKED`: no tool or data list can be established.

G12.1 emits `PROCEED`, `PROCEED WITH CONDITIONS`, `REVISE` (back to `threat`, when the built
configuration grants what the threat model didn't allow, or the eval misses the pass bar) or
`BLOCKED` (no configuration, no eval run, or no owner).

On the cap-th `REVISE` at G12, emit `RECONSIDER`: three designs in a row left a path open, so
the job's scope is the problem.

## Non-interactive runs

With no tool or data list, `agent-threat-model` emits
`BLOCKED: need the agent's tool/permission inventory`; carry it through and run no further
stages. Before the agent is built, the loop ends after `evals` with
`G12.1: awaiting the built agent's configuration and one eval run`. G12.1 never passes without
its owner.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and record that it ran degraded. A degraded `threat` still classifies every content
source as trusted or untrusted and lists each path that joins all three legs, because G12
can't be judged without them. Never skip G12 or G12.1.

## Run log (opt-in)

Only when the environment variable `SKILLDROP_LOOP_LOG` is set to a file path: after each
gate's verdict, append one JSON line to that file. Nothing else is recorded, and nothing is
sent anywhere. When the variable isn't set, or you can't read it, skip this section.

```bash
printf '%s\n' '{"ts":"2026-11-03T10:15:00Z","loop":"ship-agent","stage":"threat","gate":"G12","verdict":"REVISE","round":1}' >> "$SKILLDROP_LOOP_LOG"
```

Fields: `ts` (UTC), `loop`, `stage`, `gate` (`null` for a stage without one), `verdict` (the
gate's exact word), and `round` (1 for the first attempt, counting returns under the cap).
The log holds verdicts only: never the design, the capabilities or the findings.
`skilldrop loop-stats` summarises the file.

## Quality bar

- **The threat model inventories the design's tools,** not a generic agent's. A capability the design implies but doesn't list is modelled at its widest scope.
- **G12 passes only on architectural fixes.** "The prompt tells it not to" is not a fix for an open path.
- **Every threat-model attack is an eval case in the critical subset,** and the pass bar is set before the first run.
- **The launch review checks the built configuration against the threat model.** A grant the model didn't allow is a finding.
- **G12.1 is the owner's call.** The loop writes the decision they face; it never records their verdict.

## Anti-patterns to avoid

- ❌ **Threat-modelling before the design exists.** The model then inventories capabilities nobody chose, and misses the ones the design adds.
- ❌ **Fixing an open path with a system-prompt rule.** Injected content outranks the prompt that was meant to stop it.
- ❌ **Setting the pass bar after the first eval run.** A bar set after seeing results is chosen to pass.
- ❌ **Reviewing the configuration the design describes instead of the one the team built.** The gap between them is what the launch review is for.
- ❌ **Skipping the budget because the agent is small.** A loop with no token cap and no abort rule is how a small agent sends a large bill.
