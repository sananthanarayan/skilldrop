---
name: guide-builder
description: Turn raw notes, a spec, a thread or a messy procedure into a guide someone else can follow — a setup guide, a how-to, an onboarding walkthrough, or a reference for developers — in the length and voice its reader needs. Holds only what the notes say, marks anything inferred where it appears, orders steps so nothing is used before it is set up, and keeps open questions out of the guide so it can be sent as it stands. Use when the user wants setup or getting-started instructions, a walkthrough of how something works, or reference docs for an API or event schema — and it is NOT an SRE operational runbook (use runbook-generator) or a design proposal for review (use design-doc).
---

# guide-builder

**The rule: the guide holds only what the notes say.** A guide is followed literally. The
agent's habit is to make it feel complete: a confirmation message nobody mentioned ("you
should see *Connected*"), a menu path from a different version, "required" on every field, a
retry policy that sounds standard. Each invented detail is a step the reader will look for
and not find. So every fact comes from the material. An inference from it (a unit read off a
sample value, the likely meaning of a field) is marked as an inference where it appears:
✅ *"`ts` looks like seconds since 1970, judging by the sample; confirm before relying on
it."*

A second rule: **the guide can be sent as it stands.** Questions for the person who asked,
internal notes, "confirm with engineering" and to-do markers go in your reply, never in the
guide. Where the reader will need something the notes don't settle, the guide tells the
*reader* who to ask, if the notes say who: ✅ *"Your login for the booking system comes from
the office manager."*

## How to respond

1. **Write for the reader they named, at the size asked for.** A README section, a page for a
   new starter, a sheet for volunteers, a reference for developers: that sets the voice,
   length and shape. Short asks get short guides.

2. **Order by dependency, not by the notes.** Nothing is used before the step that sets it
   up: an account before signing in with it, a password store before the password goes in.
   Notes are usually written in the order things were remembered; the guide follows the
   order they have to be done.

3. **One action per step, with a way to tell it worked when the notes give one.** Number the
   steps. Split compound ones. Add a success check only where the notes say what success
   looks like; don't invent screens, messages or outputs.

4. **For developer references, the contract as given.** Each endpoint, event or field with
   what the notes say about it: type, whether it's required, meaning, an example where the
   notes have one. Where the notes don't say whether a field is required or what a value
   means, the reference says that, rather than guessing. Error responses only as documented.

5. **What the notes don't cover stays out.** A feature people have asked about but the notes
   don't describe, steps for a device or tool the notes never mention, a header name or host
   nobody wrote down: leave them out of the guide, and name them once in your reply.

6. **Deliver from what you have.** With notes to work from, write the guide and state any
   assumption about the reader in one line. Ask first only when there is nothing to work from.

## Quality bar

- **Every fact in the guide is in the notes;** every inference is marked where it appears.
- **The guide can be sent as written:** no questions, internal notes or to-do markers in it.
- **A reader following top to bottom never uses something before it is set up.**
- **One action per step;** success checks only where the notes give them.
- **References say "not stated" rather than guessing types, required fields or meanings.**
- **Length and voice fit the reader asked for.**

## When to use this skill

- ✅ "Write setup instructions for getting our service running locally."
- ✅ "Turn this description into an onboarding walkthrough for new staff."
- ✅ "Document these endpoints / this event schema for the developers who'll consume them."
- ✅ Converting messy notes or a spec into a doc someone can follow without you present.

## When NOT to use this skill

- ❌ SRE operational runbook — incidents, on-call escalation, deploy/rollback, SLOs → `runbook-generator`.
- ❌ Proposing a design for review/approval — options, trade-offs, risks, rollout → `design-doc`.
- ❌ Compressing a long doc for an exec audience → `exec-summary`.
- ❌ Raw unstructured mess that isn't ready to shape (a transcript, a Slack thread) → run `brief-intake` first, then come back.

## Anti-patterns to avoid

- ❌ **The plausible detail.** A success message, a default, a menu path or a retry count the
  notes never mention.
- ❌ **Notes to the requester inside the guide.** "Internal: confirm with eng before sending."
- ❌ **Steps for what the notes don't cover,** written from general knowledge because the
  reader will need them. Tell the reader who to ask instead.
- ❌ **Template sections on a small ask.** "Mental model", "Data & state", "Where it runs" for a
  five-line description.
- ❌ **"Required: yes" on every field** because the column needed filling.
- ❌ **Compound steps.** Three commands behind one number.
- ❌ **Announcing your approach.** "Reading this as a setup guide…" — just write it.
