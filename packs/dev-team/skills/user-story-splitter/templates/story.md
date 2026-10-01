# Story template

Copy per story. Keep every field; delete nothing silently — if a field is empty, say why.

```markdown
## S{n} — {Outcome noun phrase, e.g. "Shopper pays with a saved card"}

**As a** {one persona — if you need two, split the story}
**I want** {capability in the user's language, no implementation}
**so that** {the value — if you can't fill this, the story may not be worth building}

**Slice pattern:** {Path | Rules | Data | Interface | Spike}
**Depends on:** {one story ID, or —}
[assumption] {any default picked while writing this story; omit the line if none}

### Acceptance criteria (3–7; at least one edge/negative)

- **AC1** Given {precondition} When {action} Then {observable, pass/fail outcome}
- **AC2 (edge)** Given {boundary or failure precondition} When {action} Then {graceful observable outcome}

### Out of scope for this story

- {thing a reviewer will ask about} → {covered by S{m} | not covered, listed in epic out-of-scope}
```

Spike variant — replace acceptance criteria with:

```markdown
### Question this spike answers

{The single specific unknown, phrased so the answer is decidable.}

### Timebox

{e.g. 1 day. The spike ends when the timebox does, answered or not.}

### Output

A written recommendation that lets {the blocked story ID} be estimated.
```
