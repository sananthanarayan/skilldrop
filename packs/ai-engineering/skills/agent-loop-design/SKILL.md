---
name: agent-loop-design
description: Design a supervised agent loop — the generate→verify→gate cycle, observable exit criteria, hard iteration cap, human gates at irreversible steps, and failure routes — as a loop spec a team can implement in any agent harness. Use when the user wants to automate a recurring task with an AI agent loop, design a work loop / review loop / research loop, or asks "how do I stop my agent from running forever or shipping junk".
---

# agent-loop-design

You shouldn't be prompting agents; you should be designing the loops that prompt them — and a loop is only as good as its exits. This skill produces a **loop spec**: the states, gates, caps, and failure routes that turn "run the agent again until it looks right" into a system a team can trust unattended. `feature-implement-loop` is this repo's worked example of the pattern (generate → adversarial review → gate, capped at 3 rounds); this skill designs *new* loops for the user's own tasks. Fan-out inside a stage is `subagent-design`'s job; what the loop may spend is `agent-budget`'s.

## How to respond

1. **Pin the loop's job and its "done".** Ask at most 2 questions, spent on: *"what artifact does one successful run produce?"* and *"how would a human verify it's right without watching the run?"* The done-condition must be **observable** — tests pass, checklist satisfied, reviewer-agent returns zero blockers — never "output looks good". No observable done-condition derivable → the task isn't loop-ready; say what needs defining first. Non-interactive run (no user to ask): derive both from the input and tag `[assumption]`; no artifact derivable → emit `BLOCKED: need the task and its done-condition`.

2. **Draw the state machine — generate, verify, gate, and nothing mushier.**
   - **Generate**: produces or revises the artifact. Must consume the verifier's findings from the previous round as explicit input — a generate step that can't see why it failed is retry, not iteration.
   - **Verify**: judges the artifact against the done-condition. **The verifier is never the generator** — same model grading its own homework inflates; use a different persona, prompt, or agent (`devils-advocate`-style adversarial framing where quality is the risk, or programmatic checks where they exist — cheapest adequate check wins, per `llm-eval-harness`'s grading ladder).
   - **Gate**: routes on the verdict — pass → exit/handoff; fail → generate with findings; fail at cap → escalate. Every loop has exactly these three state types; "polish", "reflect", and "improve" states with no verdict are where loops go to wander.

3. **Set the caps — both of them, as numbers.**
   - **Revision cap**: max verify-fail rounds before escalation. Default 3 (`feature-implement-loop`'s cap); justify anything higher with what new information later rounds could possibly have.
   - **Budget cap**: max spend per run, referencing an `agent-budget` line (or a stated token/cost number when no budget spec exists yet, tagged `[assumption]`). A loop without numeric caps is a runaway incident scheduled for later.

4. **Place the human gates.** Every **irreversible or outward-facing action** — merge, deploy, send, publish, delete — sits behind a human gate: the loop stops and presents; it never proceeds on its own verdict. Reversible internal work (drafts, branches, scratch files) runs unattended; that's the point of the loop. Name each gate's presenter format: what the human sees must be a **decision-shaped digest** (the artifact + the verifier's verdict + what changed since the last gate), not a transcript.

5. **Design the failure routes.** Three exits, each specified:
   - **Cap hit** → escalate to a named role with a digest: rounds used, last findings, the diff of attempts. Raw logs are not an escalation.
   - **Verifier can't judge** (input outside the done-condition's domain) → route out with `BLOCKED: <what's missing>`, don't loop on it.
   - **Systemic failure** (same finding class every round) → stop early — identical findings twice means the generate step can't fix it; more rounds spend budget to relearn that.

6. **Add the telemetry row and emit** with [`templates/loop-spec.md`](templates/loop-spec.md): per-run log of rounds-used, spend, verdict, and escalations — the numbers that tell you the loop is degrading before its output does (rounds-to-pass creeping up is the leading indicator). Emit the spec in one message: state machine (Mermaid `stateDiagram-v2`), caps, gates, failure routes, telemetry. Hand off: stage fan-out → `subagent-design`; the spend model → `agent-budget`; the verifier's golden set → `llm-eval-harness`.

## Useful references in this skill

- [`templates/loop-spec.md`](templates/loop-spec.md) — state machine, caps, gates, failure-route, and telemetry skeleton

## Quality bar

- **The done-condition is observable** — a person who didn't watch the run can check it in minutes.
- **Verifier ≠ generator**, structurally: different persona, prompt, or program — stated in the spec, not implied.
- **Both caps are numbers.** "Reasonable number of iterations" is not a cap; 3 is.
- **Every irreversible action has a human gate**, and every gate has a decision-shaped digest format.
- **Generate consumes findings.** The spec shows the findings flowing into the next round's input.
- **All three failure routes are specified** — cap-hit, can't-judge, systemic — each with a destination.
- **The Mermaid renders** and contains only generate/verify/gate states plus the human-gate and escalate exits — no "polish"/"reflect" states without a verdict.

## When to use this skill

- ✅ "I want an agent to keep our runbooks up to date / triage inbound bugs / draft weekly reports — design the loop"
- ✅ "My agent keeps running forever / declaring victory on garbage" — retrofit exits onto an existing loop
- ✅ Turning a one-shot prompt that "usually works" into something a team can run unattended
- ✅ Reviewing a proposed automation for missing gates before it touches production

## When NOT to use this skill

- ❌ Implementing one feature right now — run `feature-implement-loop`; it *is* the loop
- ❌ Splitting one task across parallel agents — `subagent-design`
- ❌ Deciding what the loop may spend — `agent-budget`
- ❌ One-off tasks — a loop for something that runs once is ceremony

## Anti-patterns to avoid

- ❌ **Self-grading.** The generator's model praising the generator's output is how confident garbage ships. The verifier is a different pass with an adversarial job description.
- ❌ **Cap-free loops.** "It'll converge" is a hypothesis; the cap is what makes it a safe one to be wrong about.
- ❌ **Vibes exits.** "Loop until the output is good" defers the definition of good to the loop's most tired moment.
- ❌ **Retry cosplay.** If round N's generate can't see round N-1's findings, you built retry with extra steps — findings flow forward or the loop learns nothing.
- ❌ **Transcript escalations.** Escalating a 40-page log teaches humans to ignore escalations. Digest: rounds, findings, attempts, the ask.
- ❌ **Gating the reversible, freeing the irreversible.** Human approval for a draft file but auto-send on the customer email is the exact wrong way around — gate placement follows blast radius, not effort.
- ❌ **Loops without telemetry.** A loop that doesn't log rounds-and-spend per run degrades silently until the quarter's token bill or a shipped defect announces it.
