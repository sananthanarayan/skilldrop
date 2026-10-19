# interactive-diagram — spec reference

The spec is one JSON file. The script reads it, checks it, lays it out and writes one HTML
file. Nothing in the spec is a coordinate or a colour.

## Top level

| Field | Required | Meaning |
|---|---|---|
| `type` | yes | `architecture`, `dataflow`, `workflow`, `lifecycle`, `erd` or `sequence` |
| `title` | yes | What the map shows, in a few words |
| `question` | no | The one question the map answers; shown under the title |
| `summary` | no | The takeaway in one or two sentences; shown under the question |
| `direction` | no | `LR` (default, flow left to right) or `TB` (top to bottom). ERD and sequence are always LR |
| `groups` | no | Boxes around parts: `{"id", "label", "parent"}`. `parent` nests a group inside another |
| `nodes` | yes | The parts (for `sequence`, call them `participants`) |
| `edges` | no | The connections (for `sequence`, call them `messages`; their order is the order on the page) |
| `story` | no | A walkthrough: `[{"text", "nodes": [...], "edges": [...]}]`, three to seven steps |
| `frames` | no | Sequence only: `{"kind": "alt\|loop\|opt\|par", "label", "from": <message id>, "to": <message id>}` |
| `notes` | no | Lines shown under the text version, such as what was left out |
| `source_url` | no | Turns file citations into links, e.g. `https://github.com/org/repo/blob/<commit>/` |

Ids are unique across groups, nodes and edges. An edge without an `id` is numbered `e1`,
`e2`, … in the order written (`m1`, `m2`, … for messages); give an id to any edge a story
step or a frame names.

## Nodes

| Field | Meaning |
|---|---|
| `id` | Short, unique, never shown |
| `label` | A few words; cut on the map past about 40 characters |
| `kind` | Sets the shape and colour; see below. Defaults to the type's usual kind |
| `group` | A group id |
| `note` | One short line shown on the box (a port, a framework, a role) |
| `detail` | Longer text shown when the box is clicked |
| `fields` | ERD columns (or any list of members): `{"name", "type", "key": "pk"\|"fk"\|"uk"\|[...], "references": "table.column", "note"}` |
| `evidence` | List of citations; see below |
| `assumed` | `true` when nothing shows it; drawn dashed and listed |
| `status` | `added`, `removed` or `changed`, when marking a proposal by hand (`--compare` sets it for you) |

Kinds:

| Shape | Kinds |
|---|---|
| Box | `service`, `app`, `function`, `ui`, `client`, `job`, `worker`, `step`, `task`, `manual`, `security`, `network`, `external` (dashed border) |
| Cylinder | `datastore`, `database`, `cache`, `storage` |
| Pipe | `queue`, `topic`, `stream` |
| Person | `person`, `actor` |
| Diamond | `decision` |
| Pill | `start`, `end` |
| Rounded | `state` |
| Dots | `initial`, `final` (lifecycle start and end; the label is hidden unless it differs from the id) |
| Document | `document`, `file` |
| Table | `table`, `entity`, `view` |

## Edges and messages

| Field | Meaning |
|---|---|
| `from`, `to` | Node ids |
| `label` | What passes or happens, in a few words |
| `style` | `solid` (default), `dashed` (async, optional), `dotted` (weak reference) |
| `kind` | Sequence: `call` (default), `return` (dashed back), `async` |
| `emphasis` | `true` thickens the main path |
| `both` | `true` draws arrowheads at both ends |
| `from_field`, `to_field` | ERD: attach to these columns' rows |
| `from_card`, `to_card` | ERD: `1`, `0..1`, `*`, `1..*` shown at each end |
| `detail`, `evidence`, `assumed`, `status` | As for nodes |

## Evidence

A list of strings (or objects with the same fields):

| Form | Means | Checked with `--repo-root` |
|---|---|---|
| `"src/api.py:40-52"` | Lines 40 to 52 of that file | File exists inside the root, lines exist |
| `"src/api.py:12#PaymentIntent"` | Line 12, which contains that text | Also: the text is on those lines (case and spacing ignored) |
| `"docker-compose.yml"` | The whole file | File exists |
| `"user: anything over ten days goes to HR"` | The person's own words | Shown as a quote |
| `"doc: the runbook says failover is manual"` | A document they gave you | Shown as a quote |

Prefer line ranges with a short quote: the quote is what catches a line number that drifted.
With `--repo-root` the page shows up to 14 cited lines when a part is clicked, except from
files whose names say they hold secrets, and with secret-looking lines replaced.

## What the checks catch

Errors stop the build: unknown type, duplicate ids, an edge to a missing node, a group or
story step naming a missing id, an item with no evidence that isn't marked assumed, a cited
file that doesn't exist or is outside the root, a line range past the end of the file, a
quote that isn't on its lines. Warnings are shown on the page and in the output: unknown
kinds, long labels, parts with no connections, more than 36 parts, file citations that
weren't checked because `--repo-root` was missing.

`--check` runs the checks and writes nothing. `--json` prints the result as JSON:
`{"ok", "nodes", "edges", "assumed", "file_citations", "verified", "errors", "warnings", "output"}`.

## What the page does

- Pan (drag), zoom (scroll, or + and −), Fit.
- Click a part: its note, detail, fields, connections in and out, and its evidence with the
  cited lines. From there: what it depends on, what depends on it, its neighbours.
- Shift-click a second part: the path between them.
- Find a part by name, note or column.
- Walk through: the story, step by step (← and →); a sequence walks its messages in order.
- Light and dark, following the system setting until toggled.
- Export the diagram as SVG or PNG, and the Mermaid source (copied and downloaded).
- Deep links: `#n=<id>` opens a part, `#e=<id>` a connection, `#path=a,b`,
  `#reach=<id>,up|down`, `#step=3`, `#theme=dark`.
- The whole diagram as text in the page, read first by screen readers and by anything that
  doesn't run JavaScript; keyboard focus on every part (Tab, Enter, Esc).

## Comparing two versions

Write a spec for each version and build the newer one with `--compare older.json`. Parts and
connections only in the newer are marked added, those only in the older are drawn struck
through as removed, and a part whose label, kind, group or note changed is marked changed.
Connections match on their ends and label.

## Sequence example

```json
{"type": "sequence", "title": "Sign-in with SSO",
 "participants": [
   {"id": "u", "label": "User", "kind": "person", "evidence": ["user: people sign in from the web app"]},
   {"id": "app", "label": "Web app", "evidence": ["web/src/auth.ts:10-30#signIn"]},
   {"id": "idp", "label": "Identity provider", "kind": "external", "evidence": ["web/src/auth.ts:14#authorizeUrl"]}],
 "messages": [
   {"from": "u", "to": "app", "label": "click Sign in", "evidence": ["web/src/auth.ts:10"]},
   {"from": "app", "to": "idp", "label": "redirect with PKCE challenge", "evidence": ["web/src/auth.ts:14-18"]},
   {"id": "back", "from": "idp", "to": "app", "label": "authorization code", "kind": "return", "evidence": ["web/src/auth.ts:22"]}],
 "frames": [{"kind": "alt", "label": "code missing", "from": "back", "to": "back"}]}
```

## ERD example

```json
{"type": "erd", "title": "Orders schema",
 "nodes": [
   {"id": "customers", "label": "customers", "evidence": ["db/schema.sql:1-5"],
    "fields": [{"name": "id", "type": "uuid", "key": "pk"}, {"name": "email", "type": "text", "key": "uk"}]},
   {"id": "orders", "label": "orders", "evidence": ["db/schema.sql:7-12"],
    "fields": [{"name": "id", "type": "uuid", "key": "pk"},
               {"name": "customer_id", "type": "uuid", "key": "fk", "references": "customers.id"}]}],
 "edges": [{"from": "orders", "to": "customers", "from_field": "customer_id", "to_field": "id",
            "from_card": "*", "to_card": "1", "evidence": ["db/schema.sql:9#references customers"]}]}
```

A column whose name suggests a reference (`user_id`) but has no foreign key in the schema is
listed as a column, and any relationship drawn for it is `"assumed": true`.
