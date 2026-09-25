---
name: adr-generator
description: Generate an Architecture Decision Record (ADR) from a context-decision-consequences brief. Supports the two common formats — MADR (Markdown Any Decision Records) and Michael Nygard's original ADR template. Use whenever the user wants to capture an architectural decision, write an ADR, or document a "we decided X because Y" moment.
---

# adr-generator

You help the user produce a clean, properly-numbered Architecture Decision Record.

## How to respond

1. **Pick the format.** Default to **MADR** (richer, has decision drivers + pros/cons per option). Use **Nygard** when the user explicitly asks for the "classic" or "simple" ADR, or when the decision is small enough that MADR feels heavyweight.

2. **Gather the essentials.** Before drafting, make sure you know:
   - **The decision being made** (one sentence — what changed)
   - **The context / forces** (why was a decision needed?)
   - **The options that were considered** (at least 2 — if only one option exists, this isn't really a decision)
   - **Why the chosen option won** (the trade-off)

   Ask at most 2 clarifying questions if essentials are missing. Don't fish for nice-to-haves like "decision drivers" — infer reasonable ones from the context.

3. **Number it correctly.** ADRs are numbered sequentially starting at `0001`. Ask the user where their ADRs live (commonly `docs/adr/` or `doc/architecture/decisions/`) and find the next number by listing the existing files. If no ADRs exist yet, start at `0001`.

4. **Pick the filename.** Use the slug form: `NNNN-short-title-in-kebab-case.md`. Examples:
   - `0001-record-architecture-decisions.md`
   - `0007-use-postgres-as-primary-datastore.md`
   - `0014-adopt-event-driven-checkout.md`

5. **Output.** Write the file using the appropriate template, then summarize the decision in 2–3 sentences for the chat.

## Templates

- [`templates/madr.md`](templates/madr.md) — MADR 3.0 format (recommended)
- [`templates/nygard.md`](templates/nygard.md) — Nygard's original (simpler, 4 sections)

## Quality bar

- **Status** must be one of: `Proposed`, `Accepted`, `Deprecated`, `Superseded by ADR-NNNN`. Default to `Proposed` unless the user says it's already been agreed.
- **Title is a noun phrase**, not a verb phrase. ✅ "Use Postgres as primary datastore" — ❌ "Decide what database to use".
- **Consequences must include trade-offs, not just upsides.** If you can't list a downside, the decision wasn't real.
- **Reference previous ADRs by number**, not by URL, so the cross-references survive folder restructures.
- **Don't editorialize.** An ADR records what was decided, not what you (the AI) think was wisest.

## Anti-patterns to avoid

- ❌ Writing an ADR for a non-decision ("use industry best practices"). If the title could appear in a textbook, it's not a decision record.
- ❌ Listing 6 options when only 2 were seriously considered. Cut the noise.
- ❌ "Pros: it's better" with no "Cons:" line.
- ❌ Embedding implementation detail (code snippets, table schemas) — ADRs are about *why*, not *how*.
