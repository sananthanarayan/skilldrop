---
name: comply
description: Take a change that carries risk (a launch, a new vendor, a new use of personal data) to a risk position its owner has signed: a risk register scored inherent and residual, a DPIA when personal data is processed, the evidence behind every control the ratings rely on, a script that checks the register, and a sign-off only the named owner can give. Use when the user says "get this ready for risk sign-off", "run the comply loop", "what do we need before we can launch this", or needs a register, a DPIA and audit evidence that agree with each other.
---

# comply

One change, from its risks to a signature. Each of the three documents is useful alone. The
loop exists for the places where they disagree. A register can rate a risk low because of a
control that leaves no record. A DPIA can find a high risk to people that never reaches the
register its owner reads. An evidence map can show a gap that nobody connects to the rating
that relied on it. The loop makes the three agree. Then the register's own script checks
them, and the person who owns the risk decides.

This loop prepares material for a qualified reviewer: a DPO, a risk committee, an auditor.
It is not legal or audit advice, and every document it produces says so once, at the top.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `register` | generate | [`risk-register`](../../skills/risk-register/SKILL.md) | — |
| 2 | `assess` | generate | [`dpia`](../../skills/dpia/SKILL.md) | — |
| 3 | `evidence` | generate | [`soc2-evidence-map`](../../skills/soc2-evidence-map/SKILL.md) | — |
| 4 | `check` | verify | [`risk-register`](../../skills/risk-register/SKILL.md) | **G8** mechanical |
| 5 | `sign-off` | gate | [`doc-critique`](../../../core/skills/doc-critique/SKILL.md) | **G8.1** human |

## How to run this loop

1. **Register the change's risks.** Run `risk-register` with the change as its scope and the
   objective it threatens. Save `risk-register.csv`. Owners come from the person; a missing
   owner stays an error to resolve, never a guessed name.
2. **Screen and assess personal data.** Run `dpia` on the processing the change introduces.
   - When the screening finds no criteria that apply, keep its short screening record and go on.
   - When a DPIA is needed, complete it. Then give each risk to people still at medium or high
     residual its own register row, with the harm to people as the consequence, the same
     owner as the DPIA measure, and `DPIA` in its controls cell. The DPIA keeps scoring harm to
     people; the register row is how its owner sees it.
3. **Evidence every control the ratings rely on.** List the controls named in the register's
   residual ratings and the DPIA's in-place measures, and run `soc2-evidence-map` on that
   list. Use the organisation's SOC 2 scope when it has one; otherwise use the skill's
   default, Security only, tagged `[assumption]`.
4. **Put the evidence gaps back into the register.** A residual rating can count only
   controls that operate today. For each control the map marks `gap`:
   - set the residual likelihood and impact of every risk that relied on it back to their
     inherent values;
   - move the control to a dated action under the treatment.

   A `partial` control keeps its credit only for what its evidence covers; say what that is
   in the summary for the owner. Don't lower a rating to make a heat map look better.
5. **Check at G8.** Run the register's script on the final CSV:

   ```bash
   # Claude Code (the loop and risk-register installed side by side)
   python3 "${CLAUDE_SKILL_DIR}/../risk-register/scripts/check_register.py" risk-register.csv --top 5 --out register-check.txt
   # Other IDEs (from the folder the skills were installed into)
   python3 risk-register/scripts/check_register.py risk-register.csv --top 5 --out register-check.txt
   ```

   The exit code is the verdict: `0` is `READY`, `1` is `NOT READY`, `2` is `BLOCKED`.
   `NOT READY` returns to `register` to fix what the script names, then runs `check` again.
   Report its warnings to the person; don't edit scores to silence them.
6. **Critique, then put the decision to the owner at G8.1.** Run `doc-critique` on the
   summary the owner will read. Then show them:
   - the residual heat map from the script, as printed;
   - every risk they are asked to accept;
   - the evidence gaps and their dates;
   - the DPIA's view on prior consultation.

   Each owner accepts their own risks. A high or critical residual risk that its own owner
   accepts needs a sign-off from someone above them, named in the summary.

## Verdicts

Defined in [`contracts/terminals.json`](../../../../contracts/terminals.json).

- G8 emits `READY`, `NOT READY` or `BLOCKED`, from the script's exit code alone.
- G8.1 emits:
  - `PROCEED`: every residual risk is accepted or treated, by its named owner.
  - `PROCEED WITH CONDITIONS`: accepted, subject to named actions with dates, each recorded
    as a control and `due_date` on its risk.
  - `REVISE`: the owner rejects a rating or a treatment. Return to `register` with their reasons.
  - `RECONSIDER`: the change shouldn't go ahead as designed, for example when a residual risk
    to people stays high and the design has to change before prior consultation. The loop
    ends here.
  - `BLOCKED`: no owner is available, or the DPO's advice is required and not yet given.

## Non-interactive runs

With no person present, G8.1 cannot be satisfied. Run every stage through G8, deliver the
documents, and emit `BLOCKED: need sign-off from <the named owners>`. Never accept a risk
on someone's behalf, never fill an owner, a retention period or a vendor location with a
plausible guess, and leave the DPIA's DPO advice and decision fields blank.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and record that it ran degraded. Without `risk-register`, G8 has no script. Say so,
check the register by hand against the script's rules (every required field, owners that
name a person, residual never above inherent, dates that are dates), and mark G8 degraded.
Never skip G8.1.

## Run log (opt-in)

Only when the environment variable `SKILLDROP_LOOP_LOG` is set to a file path: after each
gate's verdict, append one JSON line to that file. Nothing else is recorded, and nothing is
sent anywhere. When the variable isn't set, or you can't read it, skip this section.

```bash
printf '%s\n' '{"ts":"2026-10-19T14:03:00Z","loop":"comply","stage":"check","gate":"G8","verdict":"READY","round":1}' >> "$SKILLDROP_LOOP_LOG"
```

Fields: `ts` (UTC), `loop`, `stage`, `gate` (`null` for a stage without one), `verdict` (the
gate's exact word), and `round` (1 for the first attempt, counting returns under the cap).
The log holds verdicts only: never a risk, an owner's name or any personal data.
`skilldrop loop-stats` summarises the file.

## Quality bar

- **The three documents agree.** Every DPIA risk at medium or high residual has a register row, and every control a residual rating relies on appears in the evidence map.
- **A residual rating counts only evidenced controls.** A control with an evidence gap gives no credit until the evidence exists, and the gap has a dated action.
- **G8 is the script's exit code.** The register reaches its owner only with zero errors.
- **Only a named owner accepts a risk.** High and critical residual risks accepted by their own owner carry a second, named sign-off.
- **Not legal or audit advice, said once.** The DPO's advice, the decision and the sign-off fields are left for the people who give them.

## Anti-patterns to avoid

- ❌ **Filing the DPIA beside the register instead of into it.** A high risk to people that isn't on the owner's list doesn't get signed off; it gets missed.
- ❌ **Leaving a residual rating on a control the evidence map marked `gap`.** That is a planned control scored as a real one, the exact thing the register bans.
- ❌ **Editing the register to turn G8 green.** Fix the risk the script names; don't delete the row or soften the score.
- ❌ **Running the evidence map on the whole SOC 2 scope.** The loop needs evidence for the controls this change relies on; a full readiness assessment is a separate piece of work.
- ❌ **Self-signing at G8.1.** A clean check says the register is well-formed. It cannot say the risk is acceptable.
- ❌ **Writing a guessed vendor location or retention period** to complete the DPIA. It stays `[to confirm: …]` and becomes a DPO question.
