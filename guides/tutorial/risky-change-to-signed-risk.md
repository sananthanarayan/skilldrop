---
title: From a risky change to a risk position its owner signs
summary: Run the comply loop on a payroll vendor move. The DPIA's risks to people join the register, two controls with no evidence lose the credit the ratings gave them, the register's own script decides G8, and the loop stops for the owner's signature.
kind: tutorial
---

# From a risky change to a risk position its owner signs

In about fifteen minutes you'll run the `comply` loop on a change that moves 420 people's
payroll to a new vendor. You'll end with a risk register, a DPIA and an evidence map that
agree with each other. You'll see two controls that leave no record lose the credit the
register gave them, and the loop stop at the one decision only the change's owner can make.

Everything quoted below is from a real run of the loop on Claude Sonnet 5 with the prompt
on this page. The loop prepares material for a DPO, a risk committee or an auditor; it isn't
legal or audit advice, and every document it writes says so.

## Install the loop

```bash
npx skilldrop-cli install --loop comply
```

This installs the loop with `risk-register`, `dpia`, `soc2-evidence-map` and `doc-critique`.

## Describe the change and the controls you have

> Run the comply loop. We're moving payroll to a new SaaS vendor, Paywell, on 1 December. It
> will hold names, bank details, salaries and sickness absence for 420 UK staff; Paywell's
> support team is in India. The HR director, Priya Shah, owns the change. Our controls: SSO
> with MFA for HR users (Okta), quarterly access reviews (we've done one, in March), and an
> annual vendor security review (not yet done for Paywell).

Name the owner and say honestly what your controls are. The loop never invents an owner.
How well each control is really running is what the evidence stage checks.

## Register the risks, then screen for a DPIA

`risk-register` writes five risks, each as cause, event and consequence, scored on a 5×5
scale. Then `dpia` screens the processing against the criteria for a DPIA. Four apply:
sickness absence is health data, the data is sensitive, it covers the whole workforce, and
employees can't freely refuse. The conclusion is a full DPIA.

The DPIA finds two high risks to people: support staff in India with unassessed access, and
no confirmed legal mechanism for the transfer. The loop gives them a row of their own in the
register, so the person signing sees them on the list they sign. Where a fact isn't known,
the DPIA marks it `[to confirm: …]` and makes it a question for the DPO. The controller's
legal name and the DPO's own advice are left blank.

## See the evidence take credit away

`soc2-evidence-map` looks only at the three controls the ratings rely on:

| Control | Status | Gap |
|---|---|---|
| SSO with MFA (Okta) | in place | — |
| Quarterly access review | partial | Only the March 2026 review has run; no review since |
| Annual vendor security review (Paywell) | gap | Never completed for Paywell |

This is the step the loop adds. A residual rating may count only controls that operate
today, so every risk that relied on the vendor review goes back to its inherent score until
the review is done. The access review keeps credit only for what its one run covered. The
register then shows the risk as it is now, not as it will be once the planned work is
finished.

## Let the script decide G8

The loop runs the register's own check on the final CSV. Its exit code is the verdict:

```text
Errors (0)
  none

Warnings (4)
  - line 2 [R-001]: treatment is reduce but residual equals inherent (15); the controls change nothing

Residual heat map, open risks (rows = likelihood, columns = impact)
  L\I |   1   2   3   4   5
    3 |   .   .   .   2   2
    2 |   .   .   .   .   1
  low 0, medium 0, high 5, critical 0

Result: PASS
```

Exit 0, so G8 is `READY`. The warnings are the evidence gaps showing through: a `reduce`
treatment whose controls don't operate yet changes nothing. Pass them to the owner as they
are. Don't adjust a score to make a warning go away. If the script had found an owner
written as "IT", or a residual above its inherent, G8 would be `NOT READY` and the loop would
go back to the register.

## Stop for the owner at G8.1

All five residual risks are high, and no one can accept them except their owner:

> **G8.1 (human gate):** **BLOCKED: need sign-off from Priya Shah** — and since all five risks
> land in the high band, accepting any of them (rather than treating it) needs a second, more
> senior sign-off that hasn't been named.

The loop also sets out the two questions that decide the outcome. Can the vendor review
and the transfer mechanism both be in place by 14 November, ahead of go-live? If they can't,
the DPIA's view is that the regulator may need to be consulted first. And who above the
owner signs any high risk that is accepted rather than fixed?

Take `signoff-summary.md` to the owner. If they reject a rating or a treatment, the loop goes
back to the register with their reasons. If the change can't go ahead as designed, the
verdict is `RECONSIDER` and the loop ends.

## What you have now

Five files that agree with each other: the register and its check, the DPIA, the evidence
map and the sign-off summary. Each residual rating counts only controls with evidence. Each
evidence gap has a date. The one decision left is named, with the person who makes it.

Next: [The loops, stage by stage](../reference/loops.md) for the `comply` diagram, or
[Use the GRC pack](../how-to/packs/use-the-grc-pack.md) to run one skill on its own.
