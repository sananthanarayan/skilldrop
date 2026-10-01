# mermaid-render reference

## Lint rules

Each rule exists because Mermaid 11.4.1's parser rejects the pattern. The script reports
`<file>:<line>: error: …`; warnings do not stop rendering.

| Rule | Applies to | Fails in Mermaid | Passes |
|---|---|---|---|
| Unknown diagram type on the first line (after front matter and `%%` lines), with a closest-match suggestion | all | `flowchar TD` | `flowchart TD` |
| Unknown flowchart direction | flowchart, graph | `flowchart LTR` | `flowchart LR`, `graph` (no direction) |
| Unquoted `(` `)` `[` `]` `{` `}` or `"` inside a node label | flowchart | `api[Orders API (v2)]`, `a{Is it (x)?}`, `A[{agent}]`, `A([Foo (x)])` | `api["Orders API (v2)"]` |
| Unquoted brackets inside a `\|pipe\|` arrow label | flowchart | `a -->\|HTTPS (443)\| b`, `a -->\|{x}\| b` | `a -->\|"HTTPS (443)"\| b`, `a -.reads (cached).-> b` |
| A shape opened and never closed | flowchart | `q{{Events} --> b` | `q{{Events}} --> b` |
| Unbalanced double quote | flowchart | `a -->\|"monthly\| b` | `a -->\|"monthly"\| b` |
| `end` as a node id | flowchart | `q --> end` | `q --> End`, `A[end]` (as a label), `endpoint` |
| Single-dash arrow `->` or `=>` | flowchart | `a -> b` | `a --> b`, `a ==> b` |
| Two nodes with no arrow between them | flowchart | `worker[Worker] cache[(Cache)]` | `worker --> cache`, `LB --> Web1 & Web2` |
| Arrow with no node on one side | flowchart | `A -->` | |
| Subgraph title with unquoted brackets | flowchart | `subgraph Billing zone (EU)` | `subgraph "Billing (EU)"`, `subgraph B["Billing (EU)"]` |
| `subgraph` with no `end`, or `end` with no subgraph | flowchart | | |
| `loop` `alt` `opt` `par` `critical` `break` `rect` `box` with no `end`; `else`/`and`/`option` outside their block | sequenceDiagram | `alt` … (no `end`) | |
| Message with no `: text` | sequenceDiagram | `A->>B` | `A->>B: call(x)` |
| Unbalanced `{` `}` across lines (ER cardinality like `\|\|--o{` is ignored) | classDiagram, stateDiagram, erDiagram | `class Foo {` (no `}`) | |
| Warning: `---oB` is read as a circle arrowhead to `B` | flowchart | | `A --- ops` (with a space) |

Labels that are fine unquoted: `&`, `:`, `/`, `%`, `<`, `>`, emoji, and the shape pairs
themselves (`[(cylinder)]`, `([stadium])`, `{{hexagon}}`, `>flag]`).

## How the rules were checked

Every rule above was run against Mermaid 11.4.1's own parser (`mermaid.parse`) in headless
Chrome, together with every Mermaid block in this repo: the `architecture-diagrams` examples
and templates, `docs/loops/*.mmd`, and the other skills' templates. The lint result (error or
clean) matched Mermaid's on all 86 cases. Two existing templates fail in Mermaid as well as in
lint, because their placeholders (`A[{agent}]`, `-->|{causal sentence}|`) are unquoted braces.
That is expected for a template with blanks still in it.

## What lint does not cover

Lint checks syntax that stops rendering, not everything Mermaid validates. Not checked:

- Diagram types other than flowchart, sequence, class, state and ER beyond the first line
  (gantt dates, pie values, gitGraph commands, C4 macros, mindmap indentation).
- Style statements (`classDef`, `style`, `linkStyle`): their CSS is not validated.
- Layout problems: a diagram that renders but is unreadable (30+ nodes, crossing edges).

When lint is clean but Mermaid still fails, run with `-o out.html --force` and open the page:
Mermaid shows its own parse error in place of the diagram.

## Rendering

| Output | With `mmdc` on PATH | Without it |
|---|---|---|
| `.svg` | Vector file, transparent background | `.html` page instead, which says so |
| `.png` | White background, 2× scale | `.html` page instead |
| `.pdf` | One PDF per diagram | `.html` page instead |
| `.html` | Always the HTML page: every diagram in order, captioned with its source line | same |

The HTML page loads Mermaid 11.4.1 from `cdn.jsdelivr.net`, pinned so the drawing does not
change under the reader, and carries a Content-Security-Policy that allows only that loader.
It needs network when opened. Install mermaid-cli for offline files:

```bash
npm install -g @mermaid-js/mermaid-cli
```

Installing mermaid-cli also downloads a headless Chrome for Puppeteer, which `mmdc` drives. In a
locked-down environment where that download is blocked, use the HTML page and print it to PDF
from a browser.
