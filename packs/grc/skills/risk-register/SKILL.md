---
name: risk-register
description: Build or update an enterprise or project risk register — each risk written as cause, event and consequence, scored for likelihood and impact on a defined scale, inherent and residual ratings, a named owner, a treatment (avoid, reduce, transfer, accept), controls, a due date and a review trigger — with a heat map, the top risks that need a decision, and a stdlib script that validates the register CSV and flags overdue reviews. Use when the user wants a risk register, a risk log, a RAID log's risk section, a heat map, or says "what are our top risks", "update the risk register", "score these risks".
---

# risk-register

You turn a list of worries into a register someone can manage: every risk has a cause, an
uncertain event and a consequence, a score on a scale written down next to it, an owner
who is a person, and a treatment with a date. The output is a CSV the user keeps, a short
summary with a heat map, and the few risks that need a decision this month. You prepare
material for a qualified risk owner or committee to review; it is not audit or legal advice.

## How to respond

1. **Ask once for what is missing, in one message.** Take what is already given. Ask for
   at most two things, and offer defaults so the user can reply "go":
   - **Scope and objective:** whose risks (a project, a business unit, the company) and
     the objective they threaten. A risk is only a risk *to something*.
   - **The existing register,** if updating: the CSV or a paste. *Default: start a new one.*
   - **Scale:** *default 5×5* (below). Use the organisation's own scale when they have one,
     and write its definitions into the output.

   Named owners, dates and control details come from the user. Never invent a person.

2. **Write each risk as cause → event → consequence.** One sentence each.
   ✅ *Cause:* "Depot laptops run an unsupported OS build" → *Event:* "Ransomware encrypts
   the depot file share" → *Consequence:* "Dispatch runs on paper for days."
   ❌ "Cyber risk." ❌ "Lack of resources." (a cause with no event) ❌ "Project delayed."
   (a consequence with no cause). Split a risk that has two independent events. Merge two
   rows that share the same event.

3. **Define the scale before scoring anything.** Default 5×5, likelihood over the review
   horizon (default 12 months), impact on the stated objective:

   | Score | Likelihood | Impact |
   |---|---|---|
   | 1 | Rare: under 5% | Minimal: absorbed in normal operations |
   | 2 | Unlikely: 5–20% | Minor: small cost or delay, no external notice |
   | 3 | Possible: 20–50% | Moderate: a milestone or budget line is missed |
   | 4 | Likely: 50–80% | Major: an objective is missed, customers or a regulator notice |
   | 5 | Almost certain: over 80% | Severe: the objective fails, or harm to people |

   Score = likelihood × impact. Bands: **low 1–4, medium 5–9, high 10–16, critical 20–25.**
   Put money or time thresholds on the impact row when the user gives them ("Major: over
   £250k or a month's delay"). Full definitions are in [`reference.md`](reference.md).

4. **Score inherent, then residual.** Inherent is the risk with no controls operating;
   residual is with the controls that exist *today*. Planned controls lower the target, not
   the residual. Residual can never be higher than inherent. If residual equals inherent
   under `reduce`, the listed controls do nothing, so say so.

5. **Pick one treatment per risk and give it a date.**
   - **avoid:** stop the activity that creates the risk.
   - **reduce:** add or strengthen controls; list them and the due date.
   - **transfer:** insurance, contract terms, outsourcing. The consequence moves; the
     accountability does not.
   - **accept:** a deliberate decision, recorded with who accepted it. A high or critical
     residual risk accepted by its own owner needs sign-off from someone above them.

   Every open risk gets a `next_review` date and a `review_trigger`: the event that reopens
   it early ("vendor misses an SLA two months running"), not "quarterly".

6. **Write the register** in the columns of
   [`templates/risk-register.csv`](templates/risk-register.csv). Controls go in one cell,
   separated by semicolons. Status is `open` or `closed`; close a risk, don't delete it.

7. **Check it with the script.** It validates required fields, score range, real owners,
   treatment values, dates, residual not above inherent, and overdue reviews and actions,
   then prints the inherent and residual heat maps and the top risks.

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_register.py" risk-register.csv --as-of 2026-10-01 --top 5 --out register-check.txt
   # Other IDEs (from the skill folder)
   python3 scripts/check_register.py risk-register.csv --as-of 2026-10-01 --top 5 --out register-check.txt
   ```

   `--scale N` changes the scale (3 to 10). Exit code 0 means valid, 1 means errors in the
   register, 2 means the file could not be read. Fix every error and rerun before
   presenting. Report warnings to the user; don't silently fix scores to make them go away.

8. **Present the summary** above the register:
   - the scale and bands, in one line;
   - the residual heat map from the script, pasted as printed;
   - **Decisions needed:** at most five risks, each with the decision and who makes it
     ("Accept R-006 flood risk at residual 8, or fund racking: Operations Director");
   - **Overdue:** reviews and actions past their date, with owners;
   - what changed since the last version, when updating.

**Non-interactive runs** (subagent, CI, headless): a missing scale or horizon becomes the
default above, tagged `[assumption]` at the top. A missing scope, or no risks to work from,
emits `BLOCKED: need the scope and objective, and the risks or the source to draw them from`.
A missing owner is written as an error to resolve, never filled with a guessed name.

## Useful references in this skill

- [`reference.md`](reference.md): scale definitions, cause-event-consequence patterns, treatment rules, review triggers, and the CSV columns
- [`templates/risk-register.csv`](templates/risk-register.csv): the register header and one annotated row
- [`scripts/check_register.py`](scripts/check_register.py): the validator and heat map (stdlib, Python 3.9+)
- [`examples/northwind-register.md`](examples/northwind-register.md): worked example, with the script's real output
- [`examples/northwind-register.csv`](examples/northwind-register.csv): the example register

## Quality bar

- **Every risk has a cause, an event and a consequence,** each a sentence. No one-word risks.
- **The scale is written down** in the output, with what each number means.
- **Inherent and residual are both scored,** and residual counts only controls in place today.
- **Every open risk has a named owner** (a person or a role a person holds) and a next review date.
- **Every treatment has an action and a date,** except `accept`, which names who accepted it.
- **The script passes with zero errors** before the register is shown, and its heat map is pasted, not redrawn by hand.
- **The decision list is short:** five or fewer, each naming the decision and the decider.

## When to use this skill

- ✅ Starting a risk register for a project, a programme, a business unit or the company
- ✅ Updating scores, owners and dates before a risk committee or steering group
- ✅ Turning a workshop's sticky notes into scored, owned risks
- ✅ Checking an existing register CSV for gaps and overdue reviews

## When NOT to use this skill

- ❌ Security threats against a specific system design, by STRIDE: use `threat-model`
- ❌ Threats specific to an AI agent's tools, prompts and data: use `agent-threat-model`
- ❌ Risks to individuals from processing personal data: use `dpia`, which scores harm to people, not to the company
- ❌ Mapping controls to SOC 2 criteria and audit evidence: use `soc2-evidence-map`
- ❌ Recording a decision once it has been made: use `decision-log`
- ❌ Setting quality targets such as availability or latency: use `nfr-spec`

## Anti-patterns to avoid

- ❌ **The one-word risk.** "Cyber", "people", "budget". Nobody can own, score or treat a category.
- ❌ **Owner "IT" or "TBD".** A department doesn't answer for a risk; the script rejects these.
- ❌ **Residual scored on planned controls.** The register then shows a risk as handled months before anything changes.
- ❌ **Likelihood without a horizon.** "Likely" over a week and over five years are different risks.
- ❌ **"Review quarterly" as the trigger.** Name the event that should reopen the risk early.
- ❌ **Everything amber.** If most risks score 9 to 12, the scale definitions aren't being used. Score against the table.
- ❌ **Deleting closed risks.** Close them with a date and keep them; the history is what an auditor reads.
- ❌ **Redrawing the heat map by hand.** Paste the script's counts so the picture matches the CSV.
