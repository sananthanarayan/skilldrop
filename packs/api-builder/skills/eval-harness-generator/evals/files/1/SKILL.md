---
name: vendor-risk-screen
description: Screen a vendor's security questionnaire and emit PROCEED, REVISE or BLOCKED with the evidence for each finding. Use when procurement asks whether a vendor can be onboarded, or when a completed security questionnaire needs a go/no-go. Do NOT use to write the questionnaire or to negotiate contract terms.
---

# vendor-risk-screen

Read a completed vendor security questionnaire and return one verdict.

## Workflow

1. Read the questionnaire. Work only from what it states.
2. Check the hard requirements: a SOC 2 Type II report or an equivalent (ISO 27001 certificate) dated within 12 months; encryption at rest and in transit; a named security contact; a breach-notification commitment.
3. Emit the verdict:
   - `PROCEED`: every hard requirement is met with evidence quoted from the questionnaire.
   - `REVISE`: a requirement is unanswered or the evidence is out of date. List what the vendor must supply.
   - `BLOCKED`: the vendor states it has no SOC 2 report or equivalent, or the questionnaire is missing.
4. List each finding with the question it came from.

Non-interactive runs: with no questionnaire, emit `BLOCKED: need the completed questionnaire`.

## Quality bar

- Never pass a vendor that has no SOC 2 report or equivalent.
- Never invent a certification that is not in the questionnaire.
- Every finding quotes the answer it rests on.

## Anti-patterns to avoid

- ❌ Treating "in progress" as holding the certification.
- ❌ Passing on the vendor's reputation instead of its answers.
