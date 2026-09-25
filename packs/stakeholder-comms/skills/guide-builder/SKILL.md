---
name: guide-builder
description: Turn raw notes, specs, or design material into an easy-to-follow guide, auto-styled to the content — a setup/quickstart, a design walkthrough, or an API/event-schema reference. Use when the user wants setup or getting-started instructions, an onboarding walkthrough of how a system works, or developer reference docs for an API or event schema — and it is NOT an SRE operational runbook (use runbook-generator) or a design proposal for review (use design-doc).
---

# guide-builder

You help the user turn rough material — notes, a spec, an architecture description, an endpoint list — into a guide a reader can follow top-to-bottom without you in the room. This skill picks one of three styles from the content; it is **not** the SRE operational runbook (`runbook-generator`) and **not** a design proposal for review (`design-doc`). It explains and instructs; it does not propose or page.

## How to respond

1. **Detect the style first, and say which you picked.** Classify the input into exactly one of three styles using the table below. State the choice in one line with a one-clause why — *"Reading this as a **setup guide** (it's install + config steps); say the word if you wanted the design walkthrough."* — so the user can redirect before you draft.

   | Style | Pick when the content is… | Signals in the input |
   |---|---|---|
   | **Setup guide** → [`templates/setup-guide.md`](templates/setup-guide.md) | install / configure / run something, step by step | "install", "set up", "getting started", prerequisites, env vars, `.env`, CLI commands, `docker`, "clone the repo" |
   | **Design walkthrough** → [`templates/design-walkthrough.md`](templates/design-walkthrough.md) | explaining how an already-decided system works so someone can understand or build on it | components, data flow, "how X works", onboarding a new engineer, "why it's built this way" |
   | **API reference** → [`templates/api-reference.md`](templates/api-reference.md) | contracts other developers code against | endpoints, request/response shapes, OpenAPI, event names, payload schemas, status codes, webhooks, Kafka/SNS topics, JSON Schema |

2. **Handle mixed content by picking the dominant style, not blending.** If the input spans two styles (e.g. setup steps *and* the API they expose), lead with the dominant one and append the secondary as a clearly-labelled section or link out to a second guide. Only ask the user which to lead with if it's a genuine 50/50.

3. **Gather only what the chosen style can't do without.** Don't run a generic intake. Cap at 2 questions, pick defaults for the rest:
   - **Setup guide** needs the *target end state* ("running locally" vs "deployed to staging") and the *prerequisites baseline*. Without an end state, a setup guide has no finish line.
   - **Design walkthrough** needs *who it's for* (new hire vs adjacent team) and *what they should be able to do after reading*.
   - **API reference** needs the *transport + auth model* and *versioning scheme*. Without auth, the examples are unrunnable.

   If the source is genuinely too thin, say so once and draft with gaps flagged as `> ⚠️ NEEDS INPUT: …` — don't invent.

4. **Fill the matching template.** Each template is ordered the way a reader actually consumes it. Don't reorder sections to match the input's order; reorder the input to match the reader's path.

5. **Apply the universal easy-to-follow rules** (these are the spine of every style):
   - **One action per step.** Number them. No compound step hiding three commands behind one number.
   - **Every step ends in a check.** "You should see `Listening on :3000`." A step with no success signal can't tell the reader whether to continue or stop.
   - **Commands are complete and paste-able.** Real flags, not pseudocode. Placeholders are unmistakable (`<YOUR_API_KEY>`, never `your-key-here` buried mid-line) and listed once up front.
   - **Lead each section with the outcome, not the backstory.** "By the end of this section the service answers on localhost." The "why" belongs in a walkthrough, not a quickstart.
   - **Front-load the happy path.** Push edge cases, troubleshooting, and teardown to the end.

## Useful references in this skill

- [`templates/setup-guide.md`](templates/setup-guide.md) — install/configure/run, prerequisites → verify → troubleshooting.
- [`templates/design-walkthrough.md`](templates/design-walkthrough.md) — mental model → components → flow → key decisions → where the code lives.
- [`templates/api-reference.md`](templates/api-reference.md) — conventions → per-endpoint/event contracts → error catalog → changelog.
- [`examples/local-setup-guide.md`](examples/local-setup-guide.md) — raw notes → a finished setup guide, showing the detection call and the verify-after-every-step discipline.

## Quality bar

- **A reader who follows top-to-bottom reaches the stated end state without leaving the doc for missing info.** Unstated prerequisites are the #1 failure — hunt them down.
- **Every command block has an expected result or a verification step.** A command with no "how do I know it worked" is incomplete.
- **Placeholders are unmistakable and listed once up front.** `<YOUR_API_KEY>`, not a real-looking string the reader pastes verbatim and wonders why it fails.
- **No forward references that break linear reading.** "See step 7" before step 7 means the order is wrong, or it needs a link.
- **API reference: every field has type + required/optional + a one-line meaning; every endpoint has ≥1 full example request and response, including at least one error response.**
- **The detected style is stated up front with a one-line why,** so the user can redirect in one message instead of getting the wrong artifact.

## When to use this skill

- ✅ "Write setup instructions for getting our service running locally."
- ✅ "Turn this architecture description into an onboarding walkthrough for new engineers."
- ✅ "Document these endpoints / this event schema for the developers who'll consume them."
- ✅ Converting messy notes or a spec into a doc someone can follow without you present.

## When NOT to use this skill

- ❌ SRE operational runbook — incidents, on-call escalation, deploy/rollback, SLOs → `runbook-generator`.
- ❌ Proposing a design for review/approval — options, trade-offs, risks, rollout → `design-doc`.
- ❌ Compressing a long doc for an exec audience → `exec-summary`.
- ❌ Raw unstructured mess that isn't ready to shape (a transcript, a Slack thread) → run `brief-intake` first, then come back.

## Anti-patterns to avoid

- ❌ Compound steps. "Install deps, configure the DB, and run migrations" as one numbered step — split into three.
- ❌ Commands with no expected output. The reader can't tell success from a silent failure.
- ❌ Backstory before the first actionable step in a setup guide. Save the "why" for a walkthrough.
- ❌ Documenting an API in prose ("it returns the user object") instead of a typed schema + example payload.
- ❌ Blending two styles into one undifferentiated doc. Pick the dominant style; link or append the rest.
- ❌ Optimistic examples that omit the error/failure responses an API consumer is required to handle.
- ❌ Reinventing `runbook-generator` (incident playbooks, on-call) or `design-doc` (alternatives, approval) — stay in the explain-and-follow lane.
