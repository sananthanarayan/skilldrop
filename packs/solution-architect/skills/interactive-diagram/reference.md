# interactive-diagram — spec reference

The spec is one JSON file. The script reads it, checks it, lays it out and writes one HTML
file. Nothing in the spec is a coordinate or a colour.

## Top level

| Field | Required | Meaning |
|---|---|---|
| `type` | yes | `architecture`, `dataflow`, `workflow`, `lifecycle`, `erd`, `sequence`, `class`, `tree`, `timeline` or `waterfall` |
| `title` | yes | What the map shows, in a few words |
| `question` | no | The one question the map answers; shown under the title |
| `summary` | no | The takeaway in one or two sentences; shown under the question |
| `direction` | no | `LR` (default, flow left to right) or `TB` (top to bottom; the default for `class`). ERD, sequence, tree, timeline and waterfall have their own layouts |
| `wrap` | no | A long left-to-right flow wraps onto rows, like text, choosing the number that keeps its text largest on a laptop screen. `false` keeps one row; a number sets how many steps go on each row |
| `groups` | no | Boxes around parts: `{"id", "label", "parent"}`. `parent` nests a group inside another |
| `nodes` | yes | The parts. `sequence` may call them `participants`, `timeline` `events`, `waterfall` `spans`, `class` `classes` |
| `edges` | no | The connections (for `sequence`, call them `messages`; their order is the order on the page) |
| `story` | no | A walkthrough: `[{"text", "nodes": [...], "edges": [...]}]`, three to seven steps |
| `frames` | no | Sequence only: `{"kind": "alt\|loop\|opt\|par", "label", "from": <message id>, "to": <message id>}` |
| `notes` | no | Lines shown under the text version, such as what was left out |
| `answers` | no | The person's questions or guesses, answered: `[{"question", "answer", "evidence"}]` (or `"assumed": true`). Shown as a table at the top of the page; evidence is checked like any other |
| `timezone` | no | Timelines: the zone times are shown in (`UTC`, `-05:00`, `+05:30`). Default: the first event's |
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
| Class box | `class`, `interface`, `abstract`, `enum`, `record` (the kind is shown as a stereotype) |
| Tree items | any box kind, plus `folder`, `module`, `package`, `capability`, `feature`, `team`, `role` |
| Timeline marks | `event`, `alert`, `change`, `action` (dots), `milestone` (diamond) |

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

For a waterfall or a timeline the script computes what the data shows and puts it at the top
of the page under **What it shows**: for a waterfall, the total, what the whole waited on most
(own work of spans on the critical path), spans that mostly wait on their children, siblings
that overlap (with the wall-clock time and the misleading sum), and spans that end after their
parent; for a timeline, the span, the longest quiet stretch, approximate times and the time
zones the sources used. Warnings about the spec are printed for whoever builds the page, never
published on it.

`--check` runs the checks and writes nothing. `--json` prints the result as JSON:
`{"ok", "nodes", "edges", "assumed", "file_citations", "verified", "errors", "warnings", "output", "reply_first_line"}`.
A successful build also prints `reply_first_line`: the titled link the reply opens with.

## What the page does

- Pan (drag), zoom (scroll, or + and −), Fit.
- Click a part: its note, detail, fields or members, facts (a span's timings, an event's time,
  how much a tree item contains), connections in and out, and its evidence with the cited
  lines. From there: everything it reaches, everything that reaches it, its neighbours (named
  for the diagram: "Everything inside it" on a tree, "What led to it" on a timeline).
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

## Class diagrams

`classes` (or `nodes`) take `members`: `{"name": "charge(amount)", "type": "Receipt", "visibility": "+"}`
(`+`, `-`, `#`, `~`, or `public`, `private`, `protected`, `package`). Each relation in `edges`
(or `relations`) has a `kind`:

| `kind` | `from` → `to` | Drawn as |
|---|---|---|
| `inherits` | child → parent | solid line, hollow triangle at the parent |
| `implements` | class → interface | dashed line, hollow triangle at the interface |
| `composition` | whole → part | filled diamond at the whole |
| `aggregation` | whole → part | hollow diamond at the whole |
| `association` | one → the other it holds | solid line, open arrow |
| `dependency` | user → used | dashed line, open arrow |

Parents and interfaces are placed above what extends them.

## Trees

Each item names its `parent` (the top item has none; several top items make a forest). Edges
are not used: the lines come from the parents. The page shows how many items each one
contains, and "Everything inside it" highlights a subtree.

```json
{"type": "tree", "title": "What the payments service is made of",
 "nodes": [{"id": "root", "label": "payments/", "kind": "folder", "evidence": ["payments/README.md"]},
           {"id": "api", "label": "api/", "kind": "folder", "parent": "root", "evidence": ["payments/api/__init__.py"]}]}
```

## Timelines

Each event has `at`, and optionally `end` (drawn as a bar) and `lane` (a group id, or any
name). Times are dates or date-times (`2026-10-03`, `2026-10-03T09:12`, with or without an
offset), times of day (`09:12`), or plain numbers, but all the same way in one spec. The axis
is to scale, except that a quiet stretch longer than about a third of the whole is shortened
and marked with how long it was, so a burst of events stays readable. `edges` between events
(`caused`, `detected`) are drawn as straight links; mark them assumed unless something shows
the link. The walkthrough steps through the events in time order.

```json
{"type": "timeline", "title": "Payment outage, 3 October",
 "groups": [{"id": "alerts", "label": "Monitoring"}],
 "events": [{"id": "a1", "label": "Card error rate above 5%", "at": "2026-10-03T09:19", "lane": "alerts",
             "kind": "alert", "evidence": ["incident.md:12"]}]}
```

## Waterfalls

Each span has `start` and either `end` or `duration`, and optionally `parent`, `service` (sets
its colour) and `status` (`error` outlines it red). Numbers are in `unit` (default `ms`);
date-times work too. The page marks the critical path (the span that finished last, the one
that finished last before that one started, and so on, inside each span), and each span's
panel gives its start, duration, share of the whole and the time not covered by a child span.
A span that runs outside its parent is a warning, because clocks on two machines disagree or
the parent is wrong. The walkthrough follows the critical path.

```json
{"type": "waterfall", "title": "Where a slow checkout spent its time", "unit": "ms",
 "spans": [{"id": "root", "label": "POST /checkout", "start": 0, "end": 1840, "service": "api", "evidence": ["trace-7f3a.json"]},
           {"id": "pay", "label": "stripe.PaymentIntent.create", "start": 430, "duration": 1190, "parent": "root",
            "service": "stripe", "evidence": ["trace-7f3a.json"]}]}
```

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
