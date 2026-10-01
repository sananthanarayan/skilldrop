---
name: mermaid-render
description: Check Mermaid diagrams for the mistakes that stop them rendering (unknown diagram type, unbalanced brackets or quotes, unquoted parentheses in labels, the word end as a node id, missing arrows, unclosed subgraphs or alt blocks) with line numbers and a fix for each, then render them to SVG, PNG or PDF with mermaid-cli, or to a standalone HTML page when it is not installed. Works on a .mmd file or every mermaid fence in a Markdown doc. Use when a diagram "won't render", the user says "check my mermaid", "export this diagram as SVG/PNG", or needs the diagrams in a doc as image files.
---

# mermaid-render

You make Mermaid diagrams render, then turn them into files. Most Mermaid failures are a
handful of syntax mistakes that the live editor reports as "Parse error on line 2" with no
hint. The lint here names the mistake, the line, and the fix. Then the script renders: with
`mmdc` (mermaid-cli) when it is installed, otherwise to an HTML page that draws the diagrams
in a browser. Diagrams usually come from `architecture-diagrams`; the rendered SVGs go into
`md-to-html` or `md-to-docx` as images.

## How to respond

1. **Ask once for what is missing.** Usually only the input:

   > Send the diagram (a `.mmd` file, or the Markdown doc it lives in). Optional:
   > 1. **Output:** `svg` (sharp at any size, best for docs) · `png` (for slides and chat) ·
   >    `pdf` · `html`. *Default: lint only, or `svg` if the user asked for a file.*
   > 2. **Where to write it.** *Default: next to the input.*

2. **Lint first, always.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/render_mermaid.py" diagram.mmd
   # Other IDEs (from the skill folder)
   python3 scripts/render_mermaid.py diagram.mmd
   ```

   For a `.md` file the script finds every ```` ```mermaid ```` fence, and line numbers refer to
   the `.md` file. Exit code 1 means at least one error.

3. **Fix each error without changing what the diagram says.** Apply the fix the lint names:

   | Lint says | Fix |
   |---|---|
   | unquoted `(` `)` in a label | ✅ `api["Orders API (v2)"]` · ❌ `api[Orders API (v2)]` |
   | arrow label has unquoted brackets | ✅ `-->|"HTTPS (443)"|` · ❌ `-->|HTTPS (443)|` |
   | `end` is reserved | ✅ `done([Done])` or `End` · ❌ `queue --> end` |
   | `->` is not a flowchart arrow | ✅ `a --> b` · ❌ `a -> b` |
   | no arrow between `a` and `b` | Add the arrow the author meant, or put the two nodes on separate lines |
   | subgraph / `alt` has no `end` | Add `end` where the block should close, judged from the indentation |
   | unknown diagram type | Use the suggested keyword (`flowchart`, `sequenceDiagram`, `stateDiagram-v2` …) |

   Show the user a before/after of each changed line. When the intent is unclear (which node
   did `worker cache` mean to connect?), ask rather than guess.

4. **Render once lint is clean.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/render_mermaid.py" design.md -o figures/design.svg
   # Other IDEs (from the skill folder)
   python3 scripts/render_mermaid.py design.md -o figures/design.svg
   ```

   - One diagram writes `design.svg`; a doc with several writes `design-1.svg`, `design-2.svg`
     … in document order.
   - `.png` renders on white at 2× scale for slides.
   - Without `mmdc` the script writes `design.html` instead, which draws every diagram with
     Mermaid 11.4.1 (pinned) from jsDelivr, and says so. Tell the user that page needs network
     when opened, and that `npm install -g @mermaid-js/mermaid-cli` gets real SVG/PNG files.
   - `--force` renders despite lint errors. Use it only to show the user Mermaid's own error.

5. **Report:** files written, any `mmdc` failure verbatim, and the fixes made.

**Non-interactive runs** (subagent, CI, headless): lint, apply only the fixes the table above
makes unambiguous, mark each with `[assumption]`, and render. If a fix needs the author's
intent (a missing arrow, where a block ends), emit `BLOCKED: need the intended <connection |
block end> at <file>:<line>` and do not render that diagram.

## Useful references in this skill

- [`reference.md`](reference.md): every lint rule, what it catches and why Mermaid fails on it, how it was checked against Mermaid 11.4.1, and what lint does not cover
- [`scripts/render_mermaid.py`](scripts/render_mermaid.py): lint and render (stdlib; `mmdc` optional)
- [`examples/broken-diagrams.md`](examples/broken-diagrams.md): real lint output on broken and clean diagrams, a fix, and the no-`mmdc` fallback

## Quality bar

- **Every error has a line number and a fix,** in the user's file, not in a temporary copy.
- **Fixes keep the meaning.** Same nodes, same edges, same labels; only syntax changes.
- **Clean diagrams pass.** The `architecture-diagrams` examples and templates lint clean, and lint never blocks a diagram Mermaid itself accepts.
- **The output format matches the use:** SVG for documents, PNG for slides and chat.
- **Network dependence is stated.** The HTML fallback is named as needing network, with the install line for real files.

## When to use this skill

- ✅ A Mermaid diagram shows "Syntax error" or "Parse error" and the user can't see why
- ✅ Exporting diagrams from a design doc as SVG or PNG for slides, Word or Confluence
- ✅ Checking every diagram in a doc before it is shared or merged
- ✅ Embedding diagrams in an HTML or Word export that must work offline

## When NOT to use this skill

- ❌ Drawing a new diagram from a description; use `architecture-diagrams`
- ❌ Converting the whole Markdown doc to a web page; use `md-to-html` (render the diagrams here first if readers are offline)
- ❌ Converting the whole doc to Word; use `md-to-docx`

## Anti-patterns to avoid

- ❌ **"Fixing" a label by deleting the parenthesised part.** Quote the label; keep the words.
- ❌ **Renaming `end` to `End` in a subgraph closer.** Only a node called `end` is the problem; the lone `end` line that closes a subgraph is correct.
- ❌ **Rendering with `--force` and shipping the result.** Mermaid draws an error graphic, not the diagram.
- ❌ **Sending the HTML fallback as if it were an SVG.** It is a web page that needs network.
- ❌ **Linting a copy and reporting line numbers from it.** Run the script on the user's own `.md` so the numbers match their editor.
- ❌ **Showing the machinery.** The reply and the artifact are for the person who asked. Don't mention this skill, its files, templates, caps or internal terms, or that the run is non-interactive. Name another skill once, at the end, as a suggested next step, never inside the artifact.
