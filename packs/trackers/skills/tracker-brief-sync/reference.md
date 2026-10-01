# tracker-brief-sync reference

## Sections: what an issue links back to

The script needs to know what counts as a section of the doc.

| Doc shape | Sections are | Flag |
|---|---|---|
| A PRD from `prd-draft`, or any doc with requirement IDs | IDs in the first column of a table, or at the start of a heading or list item (R1, G1, NFR-3) | default; `--id-pattern` sets which IDs need an issue (default `R\d+`) |
| A brief with no IDs | Every `##` and `###` heading, by its slug (`## Saved searches` → `saved-searches`) | `--headings` |

With IDs, only those matching `--id-pattern` must have an issue; other IDs (goals, NFRs) are
valid link targets but aren't required. A requirement whose MoSCoW cell is `W` (Won't have)
must **not** have an issue.

If the doc has neither IDs nor headings, ask the user to add IDs to the requirements, or to
number them, before syncing. Matching by title is too fragile to report drift on.

## The Source line

Every issue the script creates ends its description with:

```text
Source: <doc_url or doc>#<anchor> (<section>)
```

The anchor is the heading the section sits under (for IDs) or the heading's own slug (for
`--headings`). The drift check reads the part in brackets. If someone deletes the line, drift
falls back to finding the ID anywhere in the title, description or labels, and lists those
issues as "linked by mention" so the user can restore the line.

## From doc to items

| Doc part | Becomes | Rule |
|---|---|---|
| Goal | Epic | One epic per goal that has requirements mapped to it. A goal with none gets no epic; say so |
| Requirement (M, S, C) | Story or task | One per requirement. Two only if the requirement has two independent behaviours. If it's too big for one, say so and hand it to `user-story-splitter` |
| Requirement (W) | Nothing | List under "Not created" |
| Non-goal | Nothing | List under "Not created" |
| Open question | Nothing | Report it as unresolved; it may add work later |
| Quality target / NFR | Task, only if it's a piece of work (e.g. a load test); otherwise a criterion on the stories it constrains | Say which |

**Acceptance criteria** restate the requirement's observable behaviour as Given/When/Then.
They don't add behaviour the doc doesn't have. If a requirement is too vague to test ("fast",
"easy"), write the criterion you can, and list the requirement under "Needs sharpening in the doc".

**Labels** have no spaces (Jira rejects them). Use one label for the feature on every item, plus
an area label where the doc makes the area clear.

## Spec format

See [`templates/issues-spec.json`](templates/issues-spec.json).

| Field | Required | Notes |
|---|---|---|
| `doc` | yes | File name of the doc |
| `doc_url` | no | Where the team reads the doc; used in the Source line if present |
| `items[].id` | yes | Your own ID (E1, S1). Unique. Not the tracker key |
| `items[].type` | yes | epic, story, task or bug |
| `items[].parent` | no | The `id` of an epic in the same spec. Epics can't have parents |
| `items[].title` | yes | Verb-first for stories ("Pay as a guest…"), outcome for epics |
| `items[].description` | yes | From the doc; no invented reasons or numbers |
| `items[].acceptance_criteria` | stories and tasks | A list of strings |
| `items[].labels` | no | A list; no spaces |
| `items[].source` | yes | The section ID or heading slug; must exist in the doc and not be Won't have |

## Import targets

| Target | What you get | How to import |
|---|---|---|
| `--target jira` | CSV: `Issue Id, Parent Id, Issue Type, Summary, Description, Labels, Labels…` | Jira's CSV importer (external system import). On the field-mapping screen, map Issue Id and Parent Id so children link to their parent, and map every Labels column to Labels. Whether an epic link imports this way depends on your Jira; if stories land without a parent, import the epics first and set the parent in bulk after |
| `--target csv` | CSV: `ID, Type, Title, Description, Acceptance criteria, Labels, Parent ID, Parent title, Source` | Any importer with a column-mapping step. Check your tracker's current import docs for which columns it accepts. For Linear, the more dependable route is creating issues from the spec through the Linear MCP, one call per item, epics first |
| `--target github` | A bash script of `gh label create` and `gh issue create` commands | GitHub has no CSV import for issues. Read the script, then run it inside the repo. Epics become issues labelled `epic`; add children as sub-issues afterwards |

When the user has a tracker MCP tool and asks you to create the issues directly, still write
and check the spec first, then create from it, so the drift check has the same Source lines.

## Drift: what's reported

| Drift | Rule | Usual fix |
|---|---|---|
| Doc section with no issue | A required section with no live issue (cancelled and duplicate issues don't count) | Create the issue, or change the doc (move it to Won't have) |
| Issue with no doc section | No Source line and no ID mention | Add a requirement to the doc, or take the issue out of the feature |
| Issue pointing at a missing section | Its Source names a section the doc doesn't have (renumbered or deleted) | Relink, or restore the section |
| Issue for a Won't-have requirement | Its Source names a `W` requirement | Close the issue, or change the doc first |

Drift is a disagreement between two sources. The report says which way each could be resolved
and who decides; it doesn't assume the tracker is wrong.

## Field mapping for drift exports

| Field | Jira CSV | Linear | GitHub |
|---|---|---|---|
| key | Issue key | ID / identifier | number |
| title | Summary | Title | title |
| description | Description | Description | body |
| status | Status | Status / state | state |
| type | Issue Type | (labels) | (labels) |
| labels | Labels | Labels | labels |

GitHub: `gh issue list --label guest-checkout --state all --limit 500 --json number,title,body,state,labels > issues.json`.
