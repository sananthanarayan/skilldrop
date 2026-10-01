---
name: launch-readiness
description: Produce a go/no-go launch readiness report for a merged change before it goes live — one row per check (rollback path, alert and runbook per new failure mode, NFR targets measured, comms drafted, data/privacy sign-off), each with an owner, evidence link, and met / not met / n/a-because status, ending in a PROCEED / PROCEED WITH CONDITIONS / REVISE / BLOCKED verdict. Use when the user asks "are we ready to launch", "go/no-go", "production readiness review", "launch checklist", or "can we ship this to users".
---

# launch-readiness

You judge whether a change that is already merged *can* go live, using evidence rather than
reassurance. The output is a readiness report a release owner can act on in five minutes.
Whether it *should* go live now (timing, freeze windows, who is on call) is a separate human
decision. That belongs to `council-review` or the release owner, not to this report.

## How to respond

1. **Pin down what is launching.** You need: the change (a PR, a release tag, or a feature
   name), who it reaches (internal, a percentage, everyone), and the release owner. If the
   change itself is unknown, ask. You may ask at most 2 questions. A missing reach or owner
   becomes an `[assumption]` to confirm. Everything else becomes a row that is `not met`
   because evidence is missing.

2. **List the new failure modes first.** Before any checklist, write 3–5 ways this specific
   change could hurt users or data once it is live. Read them from the diff, the design doc or
   the migration plan. Each later check is judged against this list. A generic checklist with
   no failure modes is a ritual.

3. **Fill [`templates/readiness-report.md`](templates/readiness-report.md).** It has one row
   per check, and every row carries:
   - **Status:** `met`, `not met`, or `n/a — <reason>`. `n/a` without a reason counts as `not met`.
   - **Evidence:** a link, a command output, or a file path. A row with no evidence counts as
     `not met`, however confident the user sounds. Evidence must cover the path the failure
     mode touches; if it is unclear what it covered (which endpoint a load test hit), tag it
     `[assumption]`.
   - **Owner:** a role, not a person's name.

4. **Apply the checks in this order.** The order matters: the first ones are the costliest to
   discover after launch.
   1. **Rollback.** It must be a tested path back, with its data story stated. If a data or
      schema change is involved and no plan exists, hand off to `migration-plan`.
   2. **Detection.** Each new failure mode needs an alert that fires before users complain. If
      one is missing, hand off to `observability-plan`.
   3. **Response.** Each such alert needs a runbook entry. If one is missing, hand off to
      `runbook-generator`.
   4. **Quality targets.** Every target in `nfr-spec` (latency, availability, scale) must be
      *measured*, for example by a load test or canary result. A target that is only asserted
      does not count.
   5. **Data and privacy.** New personal data, retention changes or new processors need a
      named sign-off, or `n/a — <reason>`.
   6. **Comms.** User-facing notes are drafted (see `release-notes`), support is briefed, and
      the status page owner is known if the launch is risky.
   7. **Exposure.** The first exposure is staged (flag, percentage or cohort), or there is a
      stated reason why all-at-once is safe.

5. **Give the verdict.** It is the last line, with exactly one reason:
   - `PROCEED`: every row is `met` or `n/a — <reason>`.
   - `PROCEED WITH CONDITIONS`: only rows 6–7 are open, and each open row has an owner and a
     date. The open rows travel with the release.
   - `REVISE`: any row 2–5 is `not met`. Name the row and the hand-off that fixes it.
   - `BLOCKED`: rollback is `not met`, or the change or its reach is unknown. A missing
     rollback blocks on its own, whatever else passes.

**Non-interactive runs** (CI, subagent, headless): never invent evidence such as test results,
dashboards or sign-offs. Tag a guessed fact `[assumption]` and list it first. If the change
being launched cannot be identified, emit `BLOCKED: need <the PR, tag, or feature name>`.

## Useful references in this skill

- [`templates/readiness-report.md`](templates/readiness-report.md) — the report skeleton, one row per check.
- [`examples/schema-change-revise.md`](examples/schema-change-revise.md) — a worked report for a schema change that comes out `REVISE`.

## Quality bar

- **Every row has evidence or is `not met`.** Readiness asserted is not readiness.
- **The failure modes are specific to this change.** "The service could go down" is true of everything and checks nothing.
- **Rollback is judged first and can block alone.** Every other gap can be fixed while live; an irreversible launch with no way back cannot.
- **The verdict follows mechanically from the rows.** Two reviewers given the same rows reach the same verdict.
- **Owners are roles.** "Payments on-call", not a person who will change teams.

## When to use this skill

- ✅ A merged change is about to reach users and someone asks "are we ready?"
- ✅ A production readiness review needs a written go/no-go record.
- ✅ The `ready` stage of the `release` loop.

## When NOT to use this skill

- ❌ Deciding whether to *merge*. That is `pre-merge-review`'s gate, which happens earlier.
- ❌ Planning the rollout phases themselves. That is `migration-plan`; this skill checks that the plan exists and has been rehearsed.
- ❌ Choosing *when* to launch. Timing and freeze windows are the release owner's call, or `council-review`'s if they are contested.

## Anti-patterns to avoid

- ❌ **A generic checklist with every box ticked.** If no row is `not met` on a non-trivial launch, the evidence was not checked.
- ❌ **`n/a` as a way out.** Data and privacy marked `n/a` with no reason is the most common way a launch skips a review it needed.
- ❌ **Letting a strong row offset a missing rollback.** Great dashboards do not make an irreversible launch safe.
- ❌ **Writing the runbook or the alert inside this report.** Name the gap and hand it off; a readiness report that also drafts fixes becomes too long to read.
