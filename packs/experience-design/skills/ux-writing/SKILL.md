---
name: ux-writing
description: Write the interface copy for a flow or component — buttons, labels, hints, errors, empty states, confirmations, loading and success messages — as a string table where each string has its context, a character budget, a recommended version and one variant, with error messages that say what happened and what to do next, and a terminology list so the same thing has the same name everywhere. Use when the user wants UI copy, microcopy, button text, error messages, empty states, "write the strings for this screen", or "our wording is inconsistent".
---

# ux-writing

Writes the short strings people read while they are in the middle of doing something. The unit is the string, and each one is written for its exact slot: the button, the field hint, the error under the field, the empty table. The output is a string table a developer can paste from and a terminology list that keeps the product consistent. This is not `content-design`, which decides what a whole page says from user needs; ux-writing works inside a flow that already exists and fills its slots. Longer help articles and how-tos belong to `guide-builder`.

## How to respond

1. **Get the flow and the voice in one message.** Ask at most 2 questions, spent on the weakest of: *the flow or screens* (a screenshot, wireframe, component list, or step list), and *the voice* (a `brand.json` from `brand-kit`, a style guide, or three words). Default the voice to plain, direct, second person ("you"), sentence case, no exclamation marks. Default the platform to web. Say which defaults you used.

2. **List every slot before writing any copy.** Walk the flow step by step and list each string slot: page title, labels, hints, placeholders, buttons, links, errors (one per validation rule and per system failure), empty states, loading, success, confirmation dialogs, toasts. A missing error state is the most common gap; ask what each field can reject and what the system can fail on. A slot you inferred is tagged `[inferred]`.

3. **Give each slot a character budget.** Use the real width when known; otherwise default: button 20, label 30, hint 80, toast 60, dialog title 40, dialog body 160, error 100. Count characters, including spaces, and put the count next to each string. Over budget means rewrite, not truncate. Allow about 30% extra length for languages that run longer when the product is localised, and say so.

4. **Write each string for its job:**
   - **Buttons** say what happens, as a verb plus object: ✅ *"Send invite"* — ❌ *"Submit"*, *"OK"*. The confirm button in a dialog repeats the action in the title: title *"Delete this project?"*, button *"Delete project"*, not *"Yes"*.
   - **Labels** are nouns that name the data; hints say the format or the reason we ask. Placeholder text is never the only label, because it disappears on typing.
   - **Errors** say what happened and what to do, in that order, without blame: ✅ *"That email is already in use. Sign in instead, or use a different email."* — ❌ *"Invalid input"*, *"Error 409"*, *"You entered a wrong email"*. Name the field; give the fix; keep the user's input.
   - **Empty states** say what will appear here and how to make it appear, with one action: ✅ *"No invoices yet. Invoices you send will show here."* + *"Create invoice"*.
   - **Loading** says what is happening if it takes more than a moment: *"Uploading 3 of 12 files…"*, not *"Please wait"*.
   - **Success** confirms the outcome and the next step, if there is one: *"Invite sent to sam@northwind.example"*.
   - **Destructive confirmations** name the thing, the consequence, and whether it can be undone.

5. **Write one variant per string.** The variant differs on purpose: shorter, warmer, or more explicit, labelled as such. Recommend one and say why in a few words. Variants are for review and testing, not a menu for the reader to choose from without guidance.

6. **Build the terminology list.** For every concept that appears more than once (the thing being created, the people involved, the actions), pick one term and list the terms to avoid: ✅ *Use "workspace". Avoid: project, team, account.* Then check every string against it. Two names for one thing is the defect this list exists to catch; flag any existing UI or doc that already uses a banned term.

7. **Check the strings for access and tone.** Link and button text makes sense out of context (no "Click here", no "Learn more" repeated five times). Errors aren't conveyed by colour alone; say in the string what's wrong. No idioms or jokes in errors. Plain words over jargon: *"sign in"* over *"authenticate"*. This is a writing check, not an accessibility audit; send the built UI to `accessibility-audit`.

8. **Emit with [`templates/string-table.md`](templates/string-table.md)** in one message: voice and defaults used, the string table (ID, screen, slot, context, budget, recommended string with character count, variant, notes), the terminology list, and open questions (states nobody has defined yet, error cases that need engineering to confirm). String IDs follow `screen.slot.state` so developers can key them. Component-level content rules for a design system → `design-system-spec`. See [`examples/team-invite-flow.md`](examples/team-invite-flow.md).

**Non-interactive runs** (subagent, CI, headless): missing voice falls back to the default voice with an `[assumption]` line at the top; missing error cases are written as `[inferred]` and listed as open questions. If the flow itself can't be identified (no screens, steps or component named), emit `BLOCKED: need the flow or component and its steps` and write nothing.

## Useful references in this skill

- [`templates/string-table.md`](templates/string-table.md) — the string table, terminology list and open-questions skeleton
- [`examples/team-invite-flow.md`](examples/team-invite-flow.md) — worked example: a three-step invite flow, with errors, empty state and a terminology list

## Quality bar

- **Every slot in the flow has a string**, including each error, the empty state, loading and success. No "TBD".
- **Every string shows its character count against its budget**, and none is over.
- **Every error says what happened and what to do next**, names the field or object, and blames no one. No error codes on their own.
- **Buttons are verb + object.** No "Submit", "OK" or "Yes" on a primary action.
- **Each string has one labelled variant and a recommendation.**
- **The terminology list exists, and every string obeys it.** One concept, one term.
- **The voice matches the given brand or the stated default.**
- **Nothing is invented about the product.** Limits, prices, timings and policies not in the input are left as `{placeholder}` and listed in open questions.

## When to use this skill

- ✅ Writing or rewriting the copy for a flow, screen or component
- ✅ Error messages that confuse people or generate support tickets
- ✅ Empty, loading and success states nobody has written yet
- ✅ Wording that differs between screens and needs one terminology list

## When NOT to use this skill

- ❌ Deciding what a whole page or journey should say from user needs — that's `content-design`
- ❌ A help article, setup guide or walkthrough — that's `guide-builder`
- ❌ Capturing the brand's voice and visual identity — that's `brand-kit`
- ❌ Checking a built UI against WCAG — that's `accessibility-audit`
- ❌ The full component spec (states, tokens, behaviour) — that's `design-system-spec`; this skill can supply its content rules

## Anti-patterns to avoid

- ❌ **"Something went wrong."** Says nothing about what failed or what to do. If the cause is unknown, say what to try and how to get help.
- ❌ **Blaming the user.** "You entered an invalid date." Write "Enter a date after today", which is the fix.
- ❌ **"Submit", "OK", "Yes/No" on actions.** The user has to read the dialog to know what the button does.
- ❌ **Placeholder as label.** The hint vanishes on the first keystroke, and the user forgets what the field was.
- ❌ **Three names for one thing.** "Workspace" in the nav, "project" in the dialog, "team" in the email.
- ❌ **Writing to the wireframe's lorem ipsum length.** The real string runs longer, the layout breaks, and someone truncates it in code.
- ❌ **Cheerful errors.** "Oops! 🙈" on a failed payment reads as mockery.
- ❌ **Inventing the rules.** "Passwords must be 12 characters" when nobody said so. Leave a placeholder and ask.
