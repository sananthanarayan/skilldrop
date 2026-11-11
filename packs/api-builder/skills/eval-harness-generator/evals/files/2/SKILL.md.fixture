---
name: grant-budget-check
description: Check a nonprofit's grant budget against the funder's rules before it is submitted, and return PASS or FAIL with the lines that break a rule. Use when someone pastes a grant budget and asks "will this pass the funder's rules?" or "check my budget before I submit".
---

# Grant budget check

You review a draft grant budget (a list of budget lines with amounts) against the funder rules
below, before the applicant submits it.

## Funder rules

1. Indirect costs (overheads) must not exceed 10% of direct costs.
2. Equipment over 5,000 in a single line needs a written quote attached; flag any such line that
   does not mention a quote.
3. Staff costs must name a role for each salaried line, not just "staff".
4. Alcohol, fundraising events and lobbying are never fundable.
5. The budget lines must add up to the total requested. If they do not, say by how much.

## Output

Return one of three verdicts:

- COMPLIANT: no rule is broken.
- NEEDS CHANGES: one or more rules are broken but each can be fixed by editing the budget.
- REJECT: the budget asks for something the funder never pays for (rule 4).

Then list each broken rule with the budget line it applies to and the fix.

## Quality bar

- Never return COMPLIANT if any line breaks a rule.
- Indirect costs above 15% of the total budget are always a broken rule.
- Never invent a funder rule that is not listed above.
- Quote the budget line exactly as the applicant wrote it.
