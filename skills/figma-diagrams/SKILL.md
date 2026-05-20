---
name: figma-diagrams
description: Work with Figma and FigJam files via the Figma REST API — read existing file structure, list frames/pages, post comments, and produce FigJam-importable diagram specs. Use when the user mentions a Figma URL, asks to inspect/audit a Figma file, wants to comment on a design programmatically, or wants their architecture diagram in Figma.
---

# figma-diagrams

You help the user **interact with Figma files programmatically** — most often to bridge an architecture diagram from text/Mermaid into a Figma design surface their team is already reviewing in.

## Important: what's possible, what isn't

The Figma REST API is **mostly read-only for file contents**. Be honest with the user about this:

| Task | How |
|---|---|
| Read a Figma file's pages, frames, components | ✅ REST API — `GET /v1/files/:file_key` |
| List images / thumbnails of frames | ✅ REST API — `GET /v1/images/:file_key` |
| Post a comment on a file or pin to a region | ✅ REST API — `POST /v1/files/:file_key/comments` |
| Read team / project / variables | ✅ REST API |
| **Create / mutate nodes** in a design file | ❌ Not via REST. Requires the **Figma Plugin API** (runs inside Figma desktop/web) |
| Push a diagram into FigJam | ⚠️ Indirect — generate FigJam-importable JSON or have the user paste Mermaid via the "Mermaid → FigJam" community plugin |

When the user asks you to "draw this in Figma directly," set expectations up front and offer the indirect paths (Mermaid plugin, FigJam JSON spec, or plugin code that they can paste into a Figma plugin).

## Prerequisites

The user needs a Figma Personal Access Token, exported as `FIGMA_TOKEN`:

```bash
export FIGMA_TOKEN="figd_..."
```

How to get one: Figma → Settings → Security → Personal access tokens → Generate. Scope it minimally (file content read, comments write) if Figma offers granular scopes.

If `FIGMA_TOKEN` is not set, tell the user how to set it before running the scripts.

## How to respond

1. **Detect the URL.** Figma URLs look like `https://www.figma.com/file/<FILE_KEY>/<name>` or `https://www.figma.com/design/<FILE_KEY>/<name>`. Extract `<FILE_KEY>` — that's what the API takes.

2. **Pick the right script.** Helper scripts live in `scripts/` next to this `SKILL.md`:

   - `inspect_file.py <FILE_KEY>` — prints a tree of pages → frames → top-level groups
   - `list_comments.py <FILE_KEY>` — lists existing comments with author + timestamp
   - `post_comment.py <FILE_KEY> "<message>"` — adds a comment at the file root (or `--node-id N` to pin to a node)
   - `frame_to_mermaid.py <FILE_KEY> <NODE_ID>` — exports a frame's structure as a first-pass Mermaid diagram (best-effort)

   The path you use depends on where this skill is installed:

   ```bash
   # Claude Code exposes the skill's folder as $CLAUDE_SKILL_DIR
   python3 "${CLAUDE_SKILL_DIR}/scripts/inspect_file.py" <FILE_KEY>

   # In any other IDE (Cursor, Kiro, Continue, …) cd into the copied skill folder first
   cd path/to/figma-diagrams && python3 scripts/inspect_file.py <FILE_KEY>
   ```

   Dependencies (just `requests`) are declared in `manifest.json` and `requirements.txt`. Install once with:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. **For "I want my Mermaid diagram in Figma":** the cleanest path is the [Mermaid → Figma/FigJam community plugin](https://www.figma.com/community/plugin/1222021271365394457). Generate the Mermaid first (via the [`architecture-diagrams`](../architecture-diagrams/SKILL.md) skill), then guide the user to paste it. Don't pretend to push it via REST.

4. **For team audits** (e.g., "what's in our design system file?"), run `inspect_file.py` and summarize. The full JSON dump is huge — only show the user the structure that answers their question.

## Useful references

- [`reference.md`](reference.md) — Figma REST API endpoints, auth, rate limits, common gotchas
- [`templates/figjam-import.json`](templates/figjam-import.json) — example shape of a JSON spec that a FigJam plugin could consume to materialize a diagram
- [`manifest.json`](manifest.json) — declared dependencies and required env vars (read by some IDEs at install time)

## Quality bar

- **Never log the token.** Scripts use `os.environ["FIGMA_TOKEN"]`; don't pass it on the command line.
- **Don't dump 5 MB of JSON** to the user. Filter to pages/frames/groups (3 levels) and summarize.
- **Confirm before posting comments.** A comment is visible to anyone with file access — show the user the exact text and the file URL before calling `post_comment.py`.
- **Handle 429s.** The Figma API rate-limits (~25 req/min for some endpoints). If a script returns 429, back off and retry; don't loop.

## Anti-patterns to avoid

- ❌ Claiming the script "drew" something in the user's Figma file. It didn't (REST API can't).
- ❌ Asking the user to paste their token into chat. They should `export FIGMA_TOKEN=…` in their own shell.
- ❌ Posting test comments to an unfamiliar file without explicit confirmation.
