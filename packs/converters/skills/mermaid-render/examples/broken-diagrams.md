# Example: linting broken diagrams, fixing one, and rendering

Inputs are in [`inputs/`](inputs/). Every output block is what the script printed.

## 1. A flowchart with seven mistakes

[`inputs/broken-flowchart.mmd`](inputs/broken-flowchart.mmd):

```text
     1	flowchart LR
     2	    start([Customer]) --> api[Orders API (v2)]
     3	    api -> db[(Orders DB)]
     4	    api --> queue{{Events}
     5	    queue --> end
     6	    worker[Worker] cache[(Cache)]
     7	    subgraph Billing["Billing zone"]
     8	        inv[Invoicer] -->|"monthly| api
```

```text
$ python3 scripts/render_mermaid.py examples/inputs/broken-flowchart.mmd
broken-flowchart.mmd:2: error: label of `api` has unquoted `(` `)`; wrap the label in quotes: api["Orders API (v2)"]
broken-flowchart.mmd:3: error: `->` is not a flowchart arrow; use `-->` (or `==>`)
broken-flowchart.mmd:4: error: unbalanced brackets: `queue{{` is never closed with `}}`
broken-flowchart.mmd:5: error: `end` is reserved in flowcharts and breaks the diagram; use `End`, `END` or `done` as the node id
broken-flowchart.mmd:6: error: no arrow between `worker` and `cache`; join them with `-->`
broken-flowchart.mmd:7: error: subgraph opened here has no matching `end`
broken-flowchart.mmd:8: error: unbalanced double quote
lint: 1 diagram(s), 7 error(s), 0 warning(s)
```

Mermaid 11.4.1 itself stops at the first one, reporting `Parse error on line 2` and a list of expected tokens, and says nothing about the other six.

## 2. The fix

Each change is the one the lint named; the nodes, edges and labels are the same.

| Line | Before | After |
|---|---|---|
| 2 | `api[Orders API (v2)]` | `api["Orders API (v2)"]` |
| 3 | `api -> db[(Orders DB)]` | `api --> db[(Orders DB)]` |
| 4 | `queue{{Events}` | `queue{{Events}}` |
| 5 | `queue --> end` | `queue --> done([Done])` *(asked the author: "end" meant the flow finishes)* |
| 6 | `worker[Worker] cache[(Cache)]` | `worker[Worker] --> cache[(Cache)]` *(asked the author which way it points)* |
| 8 | `-->\|"monthly\| api` | `-->\|"monthly"\| api` |
| 9 | *(missing)* | `end` closing the Billing subgraph |

[`inputs/fixed-flowchart.mmd`](inputs/fixed-flowchart.mmd):

```text
$ python3 scripts/render_mermaid.py examples/inputs/fixed-flowchart.mmd
fixed-flowchart.mmd: flowchart: ok
lint: 1 diagram(s), 0 error(s), 0 warning(s)
```

## 3. Other diagram types

```text
$ python3 scripts/render_mermaid.py examples/inputs/broken-sequence.mmd
broken-sequence.mmd:5: error: `alt` block opened here has no matching `end`
lint: 1 diagram(s), 1 error(s), 0 warning(s)
```

```text
$ python3 scripts/render_mermaid.py examples/inputs/typo.mmd
typo.mmd:1: error: unknown diagram type `flowchar` on the first line. Did you mean `flowchart`?
lint: 1 diagram(s), 1 error(s), 0 warning(s)
```

## 4. Every diagram in a Markdown doc

[`inputs/design-notes.md`](inputs/design-notes.md) has three fences. Line numbers point into the `.md` file:

```text
$ python3 scripts/render_mermaid.py examples/inputs/design-notes.md
design-notes.md: diagram 1 (flowchart): ok
design-notes.md: diagram 2 (sequenceDiagram): ok
design-notes.md:31: error: `{` opened here is never closed
lint: 3 diagram(s), 1 error(s), 0 warning(s)
```

## 5. The architecture-diagrams examples lint clean

```text
$ python3 scripts/render_mermaid.py ../../../solution-architect/skills/architecture-diagrams/examples/aws-three-tier.md
aws-three-tier.md: flowchart: ok
lint: 1 diagram(s), 0 error(s), 0 warning(s)
```

```text
$ python3 scripts/render_mermaid.py ../../../solution-architect/skills/architecture-diagrams/examples/microservices-sequence.md
microservices-sequence.md: sequenceDiagram: ok
lint: 1 diagram(s), 0 error(s), 0 warning(s)
```

## 6. Rendering without mermaid-cli

On a machine without `mmdc`, asking for an SVG writes an HTML page instead and says so:

```text
$ python3 scripts/render_mermaid.py examples/inputs/checkout-flow.mmd -o checkout.svg
checkout-flow.mmd: flowchart: ok
lint: 1 diagram(s), 0 error(s), 0 warning(s)
mmdc (mermaid-cli) is not on PATH, so no .svg was written. Wrote checkout.html instead: it draws the diagram(s) with Mermaid 11.4.1 from cdn.jsdelivr.net and needs network when opened. For .svg output: npm install -g @mermaid-js/mermaid-cli, then rerun.
```

Opened in headless Chrome with network, that page drew the flowchart as an SVG. With `mmdc`
installed, the same command writes `checkout.svg`; for `design-notes.md` it would write
`design-notes-1.svg`, `design-notes-2.svg` and `design-notes-3.svg` (after the state diagram's
missing `}` is fixed).

## Rendering with mermaid-cli installed

With `mmdc` (mermaid-cli 12.0.0) on `PATH`, the same script writes real images. Run on
2026-10-01:

```text
$ python3 scripts/render_mermaid.py examples/inputs/checkout-flow.mmd -o checkout-flow.png
checkout-flow.mmd: flowchart: ok
lint: 1 diagram(s), 0 error(s), 0 warning(s)
wrote checkout-flow.png
```

The PNG is 1268 × 1442 pixels: `-s 2` doubles the scale so it stays sharp in a document.

A Markdown file with three diagrams, the third one broken, rendered with `--force`:

```text
$ python3 scripts/render_mermaid.py examples/inputs/design-notes.md -o notes.svg --force
mmdc failed on design-notes.md, diagram 3 (line 29):
Error: Parse error on line 6:
...  [*] --> Cancelled
----------------------^
Expecting 'SPACE', 'NL', 'HIDE_EMPTY', 'scale', 'COMPOSIT_STATE', 'STRUCT_STOP', 'STATE_DESCR', 'ID', 'FORK', 'JOIN', 'CHOICE', 'CONCURRENT', 'note', 'acc_title', 'acc_descr', 'acc_descr_multiline_value', 'CLICK', 'classDef', 'style', 'class', 'direction_tb', 'direction_bt', 'direction_rl', 'direction_lr', 'EDGE_STATE', got '1'
design-notes.md: diagram 1 (flowchart): ok
design-notes.md: diagram 2 (sequenceDiagram): ok
design-notes.md:31: error: `{` opened here is never closed
lint: 3 diagram(s), 1 error(s), 0 warning(s)
wrote notes-1.svg
wrote notes-2.svg
```

`--force` still writes every diagram that renders (`notes-1.svg`, `notes-2.svg`), prints
Mermaid's own parse error for the one that doesn't, and exits 1, so a CI step still fails.
Here Mermaid stopped at line 6 of that diagram, a few lines after the lint's line 31 (the
diagram starts at line 29 of the file). The lint found the cause first.

