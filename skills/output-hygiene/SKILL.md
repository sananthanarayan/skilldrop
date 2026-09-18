---
name: output-hygiene
description: Review agent-written text before it ships and strip the machine artifacts it carries — invisible Unicode, non-breaking spaces, homoglyphs, harness-added provenance trailers, trailing chat closers — then flag the prose tells a script cannot catch, each quoted with a rewrite. Use when the user wants to clean up AI-generated output, asks to remove a Claude watermark, attribution footer, or "Generated with" line, wants a draft that does not read as machine-written, or needs a pre-ship hygiene pass on a document, commit message, or pasted chat answer.
---

# output-hygiene

Surface pass over text an agent wrote. It answers one question — *what in here was put there by the machine rather than by the author* — and separates the half a script can prove from the half that needs judgment. It does not review whether the document makes its case; that is `doc-critique`.

There is no cryptographic watermark in Claude's text output, and this skill does not pretend to remove one. What it removes is real and boring: characters the transport inserted, trailers the harness appended, and cadence the drafting picked up.

## How to respond

1. **Name the target medium before reading a word of the text.** Markdown document, plain text, commit message, code comment, web form, CSV. The medium decides whether a class is a defect at all: a curly apostrophe is correct in Markdown prose and a bug in a commit message; an em dash is punctuation in an essay and a tell at four per paragraph. State the medium in the first line of the report.

2. **Run the script first, and read its output before reading the draft.** It localizes every mechanical finding, so the model pass only has to look at prose.

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/scrub.py <path> --medium <medium> --json
   ```
   In non-Claude IDEs the same file is at a plain relative path: `python3 scripts/scrub.py <path> --json`. Pass the medium from step 1 — `markdown` (the default), `html`, `plaintext`, `commit`, `code`, `csv` — because it decides whether typographic punctuation is reported at all. Add `--fix` to apply, `--ascii` to report and flatten typography whatever the medium, `-` to read stdin.

3. **Report before rewriting.** Show what `--fix` would delete, then apply it. The script's two tiers are the report's two tiers and they never merge:
   - **auto** — invisible characters, non-ASCII spacing, provenance trailers, trailing chat closers. Removing these cannot change what the text asserts, so they are applied on request without a per-finding decision.
   - **review** — homoglyphs and typographic punctuation. Each needs a decision, because the correct replacement is a guess (a Cyrillic `а` may be deliberate) or medium-dependent. Never batch-apply this tier.

4. **Check the disclosure boundary before touching the provenance class.** Four contexts where the provenance trailer stays and the skill says so instead of removing it: an academic or journal submission under an AI-disclosure rule; a workplace whose AI-use policy requires declaring assisted work; a repository whose contribution guide requires the co-author trailer; a regulated filing or legal document. The rest of the pass still runs — only the provenance class is held. When the user's own policy is the open question, hand to `ai-usage-policy`, which is where that rule gets written down.

5. **Then do the pass the script cannot: prose tells.** Read [`reference.md`](reference.md) and sweep the draft against the tell list. Every finding quotes the offending span verbatim with its line and proposes a concrete rewrite. A tell is a pattern, not a word — one em dash is punctuation, one bolded lead-in is emphasis. Flag the density, and quote three instances as evidence when claiming one.

6. **Change cadence, never content.** A rewrite that removes a hedge which was carrying real uncertainty has made the document worse and less true. Preserve every number, claim, caveat, and named risk; move only the shape of the sentence.

7. **Emit the report in this shape:**

   ```
   ## Hygiene report — <target> (<medium>)

   **Verdict:** ship as-is | clean first | disclosure check needed

   ### Machine artifacts — N auto, M review
   | line | class | what it is | action |
   |---|---|---|---|

   ### Prose tells — N
   | line | tell | quoted | rewrite |
   |---|---|---|---|

   ### Not touched
   - <what was left alone, and why>
   ```

   The **Not touched** section is mandatory. A cleaning pass that reports only what it changed is unauditable.

8. **Hand off when the problem is not the surface.** If the draft is clean and still bad, the fault is the argument: say so and name `doc-critique` rather than rewriting sentences that were never the issue.

**Non-interactive invocation:** with no text and no path, emit `BLOCKED: need the text to clean, or a path to it` — a hygiene pass over an imagined draft is fabrication. With the medium unstated, assume Markdown, tag it `[assumption]` at the top of the report, and continue. Never apply `--fix` unattended to a path the user did not name.

## Useful references in this skill

- [`reference.md`](reference.md) — the full tell taxonomy: every mechanical class with its codepoints, and every prose tell with a failing and a passing example.
- `scripts/scrub.py` — the deterministic pass. Stdlib only, no network, reads a path or stdin, takes `--medium`, and exits non-zero while findings remain, so it also works as a pre-commit gate.

## Quality bar

- **Every mechanical finding names a codepoint or quotes the matched line.** "Contains invisible characters" is unverifiable; `3:18 U+00A0 NO-BREAK SPACE` is checkable in one keystroke.
- **Every prose finding quotes the span it is judging.** The quote is the evidence. A finding that paraphrases is an opinion.
- **The auto and review tiers stay separate in the report.** Merging them means the user approves a homoglyph guess while approving a zero-width-space deletion.
- **The medium is stated before the first finding.** Half the classes are medium-dependent; a report that skips it is asserting a default it never disclosed.
- **Rewrites are paste-able.** "Tighten this" is not a rewrite. The replacement sentence is.
- **The report says what it left alone.** Including the provenance trailer when disclosure is owed, and why.

## When to use this skill

- ✅ A draft written with an agent is about to go to a customer, a board, a journal, or a public repo.
- ✅ Text pasted out of a chat window carries invisible characters that break a diff, a grep, a CSV import, or a YAML parser.
- ✅ A commit message or PR body carries a harness-added trailer the repository does not want.
- ✅ The user says the writing "sounds like AI" and wants the specific sentences named rather than a vibe.
- ✅ A pre-commit or CI gate needs a deterministic, non-zero-exit check for machine artifacts in committed prose.

## When NOT to use this skill

- ❌ The document's argument, structure, or evidence is the problem — that is `doc-critique`.
- ❌ The goal is to pass work off as unassisted where a policy requires disclosure. The skill stops on the provenance class and names the policy.
- ❌ The text is source code. Invisible-character scanning is worth running, but prose tells do not apply and the rewrite advice will be wrong.
- ❌ The user wants the text shortened or re-pitched for a different audience. That is a rewrite, not a hygiene pass.

## Anti-patterns to avoid

- ❌ **Asserting "this reads like AI" without quoting the span.** The user cannot act on a verdict they cannot locate. Every claim carries a line number and the text.
- ❌ **Laundering authorship.** Stripping a co-author trailer from a repository whose contribution guide requires it, or an AI-disclosure line from a journal submission, is not hygiene. Hold the class, name the rule, keep cleaning everything else.
- ❌ **Killing every em dash because em dashes are "a tell".** ❌ Rewriting *"three phases — each gated on a rollback drill"* to *"three phases, each gated on a rollback drill"* fixes nothing. ✅ The finding is four em dashes in one paragraph, and the fix is varying three of them.
- ❌ **Removing hedges that were carrying meaning.** ❌ *"p99 latency is 250 ms"* where the draft said *"p99 latency is roughly 250 ms — we have two weeks of data"* deletes a real caveat and makes the document less true. Strip *"it is important to note that"*; keep *"we have two weeks of data"*.
- ❌ **Auto-replacing a homoglyph with the ASCII letter that looks like it.** The word may be genuinely non-English. Report it, show the codepoint, let the author decide.
- ❌ **Re-reading the whole draft for characters the script already found.** The script is exhaustive on its classes and cheaper than a model pass. Spend the model on prose.
- ❌ **Running `--fix` and reporting only the count.** "Removed 6 artifacts" is not auditable. List them.
