---
name: user-story-splitter
description: Split an epic, feature request, or PRD chunk into independently shippable user stories with testable Gherkin acceptance criteria and a recommended build order. Use whenever the user wants to "break this down", turn an epic or PRD into a backlog, slice a feature for sprint planning, or write acceptance criteria for a story.
---

# user-story-splitter

Turns one oversized requirement into a set of vertical slices a team can ship and demo one at a time. Upstream of `feature-implement-loop` — each story this skill emits is shaped to be handed straight to it (or to a human) with no re-interpretation.

## How to respond

1. **Ingest whatever the user has.** An epic title, a PRD section, a Slack thread, a one-paragraph idea — all valid inputs. Ask at most 2 clarifying questions, and only when the answer changes how the epic is cut (e.g. "is anonymous checkout in scope?"). Everything else: pick a default and tag it `[assumption]` inline.

2. **Cut vertical slices, never horizontal layers.** Every story must deliver observable behavior end-to-end — something demoable to a non-engineer. ✅ *"Shopper pays with a saved card"* — ❌ *"Build the payments database schema"*. Use the SPIDR patterns to find the cut lines, in this order of preference:
   - **Path** — split by user path / scenario ("pay with saved card" vs "pay with new card")
   - **Rules** — relax a business rule into a later story ("any currency" → "USD only" first)
   - **Data** — subset of data first ("import CSV" before "import CSV + Excel + API")
   - **Interface** — one channel first ("web" before "web + mobile + email")
   - **Spike** — only when genuine unknowns block estimation; timebox it and state the question it must answer

3. **Make story #1 the walking skeleton.** The thinnest end-to-end path through the whole feature, even if it's embarrassingly minimal. It de-risks integration and gives every later story something working to build on.

4. **Write each story with [`templates/story.md`](templates/story.md).** Per story: Connextra statement ("As a… I want… so that…"), 3–7 Gherkin acceptance criteria, out-of-scope list, and dependencies. Every story must include **at least one negative or edge-case criterion** — a story with only happy-path ACs is not done being written.

5. **Apply the split-again rule.** A story with more than 7 acceptance criteria, more than one persona, or an "and" in its title is two stories. Split until each one fits; stop splitting when a further cut would no longer be demoable on its own.

6. **Emit the full output in one message**: a summary table (ID, title, slice pattern used, depends on, build order), then each story in full, then an **Out of scope / not covered** section listing what the epic mentioned that no story delivers — explicitly, so nothing silently disappears.

## Output shape

```markdown
# Story map: {epic title}

| # | Story | Slice | Depends on | Order |
|---|-------|-------|------------|-------|
| S1 | … (walking skeleton) | Path | — | 1 |
| S2 | … | Rules | S1 | 2 |

## S1 — {title}
**As a** … **I want** … **so that** …
[assumption] {any defaults picked}

### Acceptance criteria
- **AC1** Given … When … Then …
- **AC2 (edge)** Given … When … Then …

### Out of scope
- … (covered by S3)

## Out of scope / not covered by any story
- …
```

## Useful references in this skill

- [`templates/story.md`](templates/story.md) — the per-story skeleton
- [`examples/notifications-epic.md`](examples/notifications-epic.md) — worked example: a 2-paragraph epic split into 5 stories

## Quality bar

- **Every story is demoable to a non-engineer.** If the demo is "look at this table in the database", it's a horizontal slice — re-cut it.
- **Every acceptance criterion is pass/fail without interpretation.** A tester who has never seen the epic can verdict it. ✅ *"Then the order total shows the discounted price within 2s"* — ❌ *"Then the discount works correctly"*.
- **Dependency graph is a chain or shallow tree, never a web.** No story depends on more than one other story; if it needs two, the cut is wrong.
- **Assumptions are tagged, not embedded.** Every default the skill picked appears as a visible `[assumption]`, so planning can challenge it.
- **The epic is fully accounted for.** Everything in the input is either inside a story or named in "Out of scope / not covered" — no silent drops.

## When to use this skill

- ✅ An epic or feature request too big to estimate or fit a sprint
- ✅ Turning a PRD section into backlog items before planning
- ✅ Writing acceptance criteria for an existing vague story
- ✅ Producing input for `feature-implement-loop` — each emitted story is shaped for it

## When NOT to use this skill

- ❌ The work has no user-visible behavior (pure refactor, dependency bump) — write a task list, not stories
- ❌ The story is already small and clear — go straight to `feature-implement-loop`
- ❌ Estimating effort in hours/points — this skill orders and sizes by slice, it does not estimate
- ❌ Writing the implementation — hand the story off instead

## Anti-patterns to avoid

- ❌ **Horizontal layer stories** — "API story", "DB story", "UI story". Three un-demoable thirds of one real story.
- ❌ **Acceptance criteria that restate the story.** "Given the feature exists, when used, then it works" verifies nothing.
- ❌ **Implementation details inside Gherkin.** ❌ *"When the user clicks `#submit-btn`"* — ✅ *"When the shopper confirms the order"*. ACs describe behavior, not DOM.
- ❌ **A "misc / cleanup / polish" story** as a dumping ground for everything that didn't fit. Re-cut, or move it to out-of-scope.
- ❌ **Splitting below the demoable threshold.** Fifteen confetti stories when six would ship is coordination overhead, not agility.
- ❌ **A spike without a question.** Every spike states the specific unknown it resolves and a timebox; "investigate the architecture" is neither.
