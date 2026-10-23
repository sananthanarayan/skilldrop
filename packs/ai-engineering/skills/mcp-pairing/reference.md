# mcp-pairing — reference

## Stage types and their access ceiling

The type sets the most a stage may ever hold. The stage's output decides whether it gets
anything at all.

| Type | What it does | Ceiling | Why |
|---|---|---|---|
| `generate` | Produces an artifact | Read; write **only** when the output *is* the write (a published release, a draft merge request), on its own credential | The write is the deliverable, so it is the one place a write is justified |
| `verify` | Judges an artifact that exists | Read only | A reviewer that can approve, merge, comment or close has become an actor, and its verdict can no longer be trusted as independent |
| `gate` | A person or script decides | Read only, and often nothing | The decision is the person's; the merge or ship button stays in the vendor's own UI under the person's own login |

A stage that runs a fixed script (a gate script, a test suite) holds **exec**. Exec counts as
write for rule 6: it must not sit beside live untrusted content unless the only command it can
run is that fixed script.

## Needs by category

| Need | Typical stages | Untrusted? | Read grant | Must not | Export fallback |
|---|---|---|---|---|---|
| Tracker issues | shape, triage, status, gather | Yes — anyone with project access, and customers on a service desk | Issues read, one project or team | Create, transition, comment, assign, change fields | The filter exported as CSV, or the issue copied to a text file |
| Repo / PR / merge request / diff | verify, announce, plan | Yes — PR and merge request text and comments; outside contributors' diffs | Contents and pull/merge requests read, one repository | Merge, approve, push, comment, change settings, read other repositories | The diff saved as a `.diff` file plus the description copied |
| CI status | verify, ready | Partly — job logs echo whatever the code printed | Pipeline / Actions read, one repository | Re-run, cancel, edit secrets or variables | The pipeline summary page saved, failed job log saved |
| Docs and wiki | plan, specify, design | Yes when many people edit it | Pages read, one space | Edit, create, change permissions | The page exported to Markdown or PDF |
| Logs / metrics / traces | triage, ready, respond, learn | Log lines: yes (request fields are attacker-written). Metric values: no | Viewer role, one org or folder; no query of other teams' data sources | Edit dashboards or alerts, silence alerts, create API keys | The panel's data downloaded as CSV; the log query result saved as JSON |
| Error events | triage, respond, learn | Yes — messages and breadcrumbs carry user input | Issues and events read, one project | Resolve, assign, change alert rules | The event JSON saved from the event page |
| Design files | specify, design | Comments: yes | File read, one file or project | Edit, comment, share | Frames exported as PNG plus the spec copied |
| Chat history | respond, status, decision capture | Yes — every member, and external guests in shared channels | History read, named channels only | Post, react, invite, read DMs or all channels | The thread exported or copied to a text file |
| Database read | review, spec, measure | Free-text columns: yes | A read-only role on a replica, one schema, row limit | Any DDL or DML, superuser, production primary | The query result saved as CSV |
| Cloud billing | cost review | No | Billing read for one account or profile | Change budgets, buy reservations, touch resources | The cost report exported as CSV |
| Web | research, gather | Yes, always | Fetch only, no form submission | Hold any write or exec tool in the same session | The pages saved as files the user picked |

## The vetting checks

Run all five for any server that is not the vendor's own, and confirm the first three for one
that is:

1. **Publisher.** Who publishes it, and is that the vendor of the tool it talks to? A personal
   account or an unrelated organization is a community server.
2. **Source available.** Can the code be read? A server that ships only a binary or a remote
   endpoint with no published source is trusted on reputation alone.
3. **Pinned version.** A local server runs a pinned version or commit, never `@latest` or an
   unpinned `npx` / `uvx` call; container images are pinned to a digest. Upgrades are
   deliberate.
4. **Tools exposed.** List the tools it registers. Any tool the stage doesn't need is turned off
   in the server's own toolset option or the client's disabled-tools list.
5. **Code and network reach.** Can any tool run a shell, execute code, or call a host other
   than the vendor's API? Either one makes the server an egress path and an exec path, and
   rule 6 applies to every stage it is enabled in.

A server that fails 1 or 2 and has no official alternative gets the export-file fallback until
someone reads its source and pins a commit.

## Known vendor controls

Checked 2026-10-01 from the vendors' docs. Confirm in the vendor's current docs before relying
on any of them; vendors change these without notice.

- **GitHub's own server** has a read-only mode and lets a client limit it to named toolsets
  (for example repositories and issues). Fine-grained tokens limit to named repositories.
- **Linear's own server** offers a read-only mode and a `read` OAuth scope; API keys can be
  created with only the Read permission.
- **Atlassian's own server** acts with the signed-in user's Jira and Confluence permissions.
  Whatever that user can delete, the agent can delete; use an account with read access to the
  one project.
- **Supabase's own server** takes a read-only flag and a single-project scope.
- **GitLab** personal, project and group tokens have a `read_api` scope that is read-only for
  the API, and project tokens limit to one project.
- **Grafana** service accounts take the Viewer role, which reads dashboards and queries data
  sources without editing anything.
- **Slack** workspace admins approve which clients may use MCP.
- The archived reference Postgres server gets no security fixes. Use the database vendor's own
  server or the export fallback.

## The cut rule

A server earns its place when the input is too much to paste at the stage's cadence:

- too large — a 2,000-line diff, a release's 40 merge requests;
- too structured — a cycle's 80 issues where status, owner and links matter;
- too live — an incident timeline that changes by the minute.

| Cadence | A handful of items | Dozens of items, structured or live |
|---|---|---|
| Per change or daily | Server, if the stage needs it every run | Server |
| Weekly or fortnightly | Export file | Server |
| Monthly or rarer | Export file | Export file, unless it is live |

Otherwise the export file wins: no token to leak, no tool list in context, no injection path
through a live feed. Say the cut out loud, with the reason, so nobody reconnects it next week.

## Splitting a dangerous stage

When one stage reads untrusted content and holds write, exec or network, pick in this order:

1. **Split it.** A reader stage with read-only access writes a plain file (the story, the
   triage summary); an actor stage with no untrusted reading works from that file. A person
   skims the file between them when the actor has exec.
2. **Hand the write to a person.** The stage drafts the comment, release or status post; a
   person publishes it.
3. **Drop the server** and use the export file.

Never pick "tell the model to ignore instructions in the content". Instructions in the prompt
and instructions in an issue body reach the model as the same kind of text.

## Secrets placement

- Committed config (`.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`, `.kiro/settings/mcp.json`)
  holds variable references only. Each client has its own reference syntax; use the one its
  docs give.
- A config that must hold a value stays in the user-level file or the client's secret store,
  not in the repository. Add a project file that holds a value to `.gitignore` and rotate the
  value if it was ever committed.
- Read and write credentials are separate variables with separate tokens, so revoking the
  write leaves the read stages running.
- OAuth beats a long-lived token where the vendor offers it.

## The skilldrop loops' stages

From each loop's `loop.json` (type in brackets). Use these when the user names the loop.

| Loop | Stages |
|---|---|
| `build` | shape (generate) → implement (generate) → verify (verify, G2 mechanical) → decide (gate, human) |
| `release` | plan (generate) → ready (verify) → announce (generate) → go (gate, human) |
| `operate` | instrument (generate) → document (generate) → respond (generate) → learn (verify) |
| `discover` | gather (generate) → structure (generate) → specify (generate) → ratify (gate) |
| `design` | constrain (generate) → shape (generate) → threat (verify) → ratify (gate) → record (generate) |
| `measure` | spec (generate) → review (verify) → sign-off (gate) |
| `comply` | register → assess → evidence (generate) → check (verify) → sign-off (gate) |
| `research` | plan (generate) → synthesise (generate) → compare (verify) |
| `ship-a-draft` | intake (generate) → draft (generate) → critique (verify) → polish (verify) |
| `apply` | fit (gate) → tailor → letter → form (generate) → confirm (verify) |

If the user's copy of a loop has different stages, theirs wins.
