# Interview-kit template

One kit per stakeholder. 30-minute shape: episode opener → ranked questions → kill-question → referral close. Capture verbatim quotes — they become `prd-draft` evidence tags.

```markdown
# Interview kit: {feature idea}

**Stakeholders covered:** {list — only those holding open unknowns}
**Already known (don't re-ask):** {evidence that exists: analytics, tickets, prior research}

---

## Kit: {stakeholder role, e.g. "End user — support agent"}

**Holds the unknowns about:** {what only this person can answer}
**Time:** 30 min · **Record verbatim quotes**

### Opener (end users: concrete recent episode, never "typically")

1. "Walk me through the last time you {did the task}. Every tool you touched, start to finish."
   - *informs:* {decision} · *if {answer-shape} then:* {how the design moves}

### Ranked questions (≤7 total including opener and kill-question)

2. "{question}"
   - *informs:* {decision} · *if X then:* {design consequence}
3. …

### Kill-question (mandatory)

n. "If this never gets built, what would you do instead — honestly, how bad is that?"
   - *a kill-answer looks like:* {e.g. "shrug + existing workaround under 2 min" → feature shrinks or dies; write it down, don't soften it}

### Close

- "Who else should I talk to who'd see this differently?"
- "What didn't I ask about that I should have?"

---

## Assumptions-to-validate ledger

| Assumption the idea rests on | Validated by (stakeholder · Q#) | Falsified if |
|---|---|---|
| {e.g. agents lose ≥15 min/ticket to tool-switching} | end user · Q1 | episode shows < 5 min or a fast workaround |
| {assumption no interview can falsify} | ⚠ not interview-validatable | needs {data pull / prototype} instead |

## Synthesis path (the kit isn't done until this runs)

1. Each interview's notes → `brief-intake` (one brief per interview; quotes verbatim).
2. Merge briefs; conflicts between stakeholders are surfaced as open questions, not averaged away.
3. Decisions and follow-ups → `decision-log`. Requirements → `prd-draft`.
```

## Question-shape cheat-sheet

| ❌ Don't ask | ✅ Ask instead |
|---|---|
| "Would you use a dashboard that…?" | "What did you do the last time you needed {that info}?" |
| "Is X a problem for you?" | "Tell me about the most recent time X happened." |
| "What should we build?" | "What's the most annoying part of {task} today?" |
| "How often does X typically happen?" | "When did X last happen? And before that?" |
| "Do you agree this would save time?" | "What would have to be true for you to stop using {workaround}?" |
