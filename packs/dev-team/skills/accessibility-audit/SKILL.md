---
name: accessibility-audit
description: Adversarially audit a UI (component code, page markup, screenshot, or flow) against WCAG 2.2 AA — findings cited to specific success criteria, centered on the user and assistive tech each one blocks, severity-tagged, with a concrete fix and what a scanner would miss. Use when the user wants an accessibility review, a11y audit, WCAG check, or to find what blocks screen-reader / keyboard / low-vision users before shipping.
---

# accessibility-audit

Finds the barriers that lock real people out of a UI — and cites the exact success criterion, names the assistive tech that hits the wall, and separates what an automated scanner catches from what only a human with a screen reader will. The UI counterpart to `devils-advocate` (code), `doc-critique` (docs), and `threat-model` (designs): one adversarial pass, severity-tagged, evidence-first. Automated tools catch perhaps a third of WCAG issues; this audit is built for the other two thirds.

## How to respond

1. **Establish what's auditable from the input, and say what isn't.** Inputs vary in what they reveal:
   - **Component/page code or markup** — the richest: roles, labels, semantics, focus management, tab order are all inspectable.
   - **Screenshot/image** — visual only: contrast, target size, text-as-image, visible focus *if* captured. Keyboard behavior, screen-reader output, and focus order are **not** observable — list them as "must verify with live AT", never guess a pass.
   - **A described flow** — reason about it, flag the checks that need the real thing.
   Default standard is **WCAG 2.2 level AA**; note if the user wants A or AAA. State the input's coverage limits up front so a clean section never reads as a guarantee it can't be.

2. **Sweep all four POUR principles** using the success-criterion catalog in [`reference.md`](reference.md) — Perceivable, Operable, Understandable, Robust. Don't transcribe the catalog; run it as a lens and report only what the UI actually fails or can't be verified for. The high-yield manual checks scanners miss, swept explicitly: **keyboard-only operability** (every interactive element reachable and operable, visible focus, no traps, logical order), **screen-reader semantics** (name/role/value, headings, landmarks, alt-text *quality* not just presence), **meaningful sequence and focus order**, **error identification and recovery**, **reflow/zoom to 400%**, **target size (2.2)**, and **motion/animation** preferences.

3. **Center every finding on the user it blocks and the AT involved.** A finding without a victim is abstract. ✅ *"Submit button is a `<div>` with a click handler — keyboard users cannot reach or activate it (Tab skips it, Enter does nothing), and a screen reader announces nothing actionable. Blocks: keyboard-only and screen-reader users from completing checkout."* — ❌ *"Button not accessible."* Name the assistive tech (VoiceOver/NVDA/JAWS, keyboard-only, 400% zoom, switch control, reduced-motion) so the fix is testable.

4. **Cite the specific success criterion** — number, name, level — for every finding: `1.4.3 Contrast (Minimum) [AA]`, `2.1.1 Keyboard [A]`, `4.1.2 Name, Role, Value [A]`, `2.4.7 Focus Visible [AA]`, `2.5.8 Target Size (Minimum) [AA]`. "Make it accessible" is not a finding; a criterion citation is what makes it actionable and arguable.

5. **Severity-tag with the shared markers**, by impact on task completion:
   - 🟥 **blocker** — a user group cannot complete the task at all (keyboard trap, unlabeled critical control, contrast that renders text unreadable, a form that can't be submitted via keyboard).
   - 🟧 **major** — significant barrier with a painful workaround (poor focus order, vague link text, missing error association).
   - 🟨 **minor** — friction, not a wall (redundant alt text, a non-essential decorative image with empty-but-present alt).
   - ⚪ **nit** — best-practice polish.
   If everything is a blocker, the severity call failed — calibrate to whether the task can actually be completed.

6. **Compute contrast and sizes where the input allows it.** Given colors, state the actual ratio against the 4.5:1 (normal) / 3:1 (large) threshold: ✅ *"`#767676` on `#fff` = 4.54:1, passes AA for normal text by a hair; fails for the 14px placeholder which needs the same 4.5:1 and gets it — but `#999` on `#fff` = 2.85:1 fails."* Numbers, not eyeballing.

7. **Separate scanner-catchable from human-only**, explicitly, per finding (tag `[auto]` vs `[manual]`). It tells the team what to gate in CI (axe/Lighthouse) and what needs the screen-reader pass that no tool replaces — and it's honest that the audit's manual findings are the ones a pipeline won't keep catching. End with a **"what's solid"** section (the patterns done right, so they're preserved on refactor) and a prioritized fix order.

8. **Emit in one message**: coverage note (input limits), findings grouped by severity with SC citation + affected user/AT + `[auto]`/`[manual]` + concrete fix, contrast/size computations, what's solid, and the must-verify-with-live-AT checklist for anything the input couldn't confirm.

## Useful references in this skill

- [`reference.md`](reference.md) — the WCAG 2.2 AA success-criterion catalog by POUR, the affected-user/assistive-tech map, the severity rubric, and the "what automated tools miss" list
- [`examples/login-form.md`](examples/login-form.md) — worked example: a login form component audited to severity-tagged findings

## Quality bar

- **Every finding cites a specific success criterion** (number + name + level). Uncited "issues" are opinions.
- **Every finding names the user group and assistive tech it blocks.** No victim, no finding.
- **Severity reflects task-completion impact**, calibrated — not everything is a blocker, and a real keyboard trap is never a minor.
- **Contrast and target-size claims are computed numbers** against the threshold, not visual guesses.
- **Coverage limits are stated** and unverifiable checks are listed as must-test-with-AT, never silently passed. A screenshot audit never claims keyboard operability is fine.
- **`[auto]` vs `[manual]` is tagged**, so CI-gateable findings are separated from the human-only ones.
- **"What's solid" is present**, so good semantics survive the next refactor.

## When to use this skill

- ✅ Auditing a component, page, or flow against WCAG before shipping
- ✅ "Is this accessible? / find the a11y issues" for real markup, a screenshot, or a flow
- ✅ Pre-launch accessibility gate, or fixing a failed audit
- ✅ Reviewing a design/screenshot for the accessibility issues catchable before build

## When NOT to use this skill

- ❌ Setting the accessibility *target* (which WCAG level, on which scope) — that's `nfr-spec`
- ❌ General code correctness/security review — that's `devils-advocate`
- ❌ Writing the component — fix findings in your normal build loop, or hand to `feature-implement-loop`
- ❌ A full certified VPAT/conformance attestation — this audit feeds one, but legal sign-off is a formal process beyond a review

## Anti-patterns to avoid

- ❌ **"Make it accessible" findings.** Uncited, unactionable, unarguable. Every finding pins a success criterion.
- ❌ **Faulting alt-text presence, not quality.** `alt="image"` passes a scanner and fails a human; `alt="chart"` on a data chart conveys nothing. Audit what the alt *says*.
- ❌ **Claiming keyboard/SR passes from a screenshot.** You cannot see focus order or AT output in a PNG — list them as must-verify, don't invent a pass.
- ❌ **Severity inflation.** Tagging a decorative-image nit as a blocker burns the credibility the real keyboard trap needs.
- ❌ **Eyeballing contrast.** "Looks low" isn't a finding; "2.85:1, fails 4.5:1 AA" is.
- ❌ **Scanner-only thinking.** Reporting only what axe would catch and calling it an audit — the two-thirds it misses (focus order, label accuracy, meaningful sequence, error recovery) is where users actually get stuck.
- ❌ **Color as the only signal flagged once.** Reliance on color (1.4.1) shows up in status, charts, form errors, links-in-text — sweep every instance, not the first one.
