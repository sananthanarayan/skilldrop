---
name: mcp-pairing
description: Recommend which MCP servers to connect for a loop, workflow or task, stage by stage, with the narrowest access that works — what outside context or action each stage needs, the server that provides it (only ones the user named or the vendor officially publishes), the scopes to grant (read-only by default, never write on a review or gate stage), what it must not be able to do, the export-file fallback that keeps the stage running without it, and which stages need no server at all. Use when the user asks "which MCP servers should we hook up for this loop", "what should our agent connect to", "what token scopes does this stage need", "is this MCP setup too broad", or wants to wire GitHub, GitLab, Jira, Linear, Slack, Sentry, Grafana or a database into an agent workflow.
---

# mcp-pairing

Turns a loop, workflow or task into a per-stage connection plan: which stages get an MCP
server, which get none, and the exact access each one holds. An MCP server is a capability
handed to the agent with someone's credentials, so the default answer for every stage is
**fewer servers, read-only, scoped to one project**, and every grant beyond that is argued
from the stage's output. The plan stays honest about names: it never invents a server,
package or URL.

Complements `agent-threat-model`, which audits a finished capability surface for data
exfiltration paths. This skill decides what the surface should be in the first place;
that one attacks it.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the plan in plain words: how many servers, which ones, read or write, and which stages need none. The table comes after.
- **Use only what you were given.** Name only the tools, servers, stages and scopes the input contains, plus vendors' own official servers under the naming rule in step 3. Never invent a package, endpoint, URL or version. What the plan needs and doesn't have is listed once at the end under "To confirm".
- **Deliver from what you have.** When the request names a loop, workflow or task, state the assumptions in a line and produce the plan. When it names nothing to pair, ask for it in one or two plain sentences and say what the plan will contain once it arrives.
- **Write for someone who has never heard of this skill.** No skill names, no paths from this folder, no internal terms, nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.

1. **List the stages and what each one produces.** From a named skilldrop loop, use its stage list and the stage types in [`reference.md`](reference.md) (generate, verify, gate). From a described workflow, write the stages as verbs with one output each — ✅ *"triage: one ticket labelled with severity"* — ❌ *"handle tickets"*. Mark each stage's **type** and its **cadence** (per change, daily, weekly, monthly). Ask at most 2 questions, spent on the tools in use and who can write into them; everything else is tagged `[assumption]`.

2. **Name the outside context or action each stage needs, by category.** Categories: tracker issues, repo / merge request / diff, CI status, docs and wiki, logs / metrics / traces, error events, design files, chat history, database read, cloud billing, web. A stage that works from the previous stage's output needs nothing outside — write **None** and move on. ✅ *"implement — None: works from the shaped story and the local checkout"*.

3. **Pick the server for each need, or write the category.** Name a server only when (a) the user named it, or (b) it is the vendor's own server for a tool the user named — then say how to confirm it: publisher is the vendor, source or docs live on the vendor's domain or organization, and a version or commit is pinned for a local server. Never write a URL, package name or install command the user did not give. ✅ *"GitLab's own MCP server — confirm GitLab publishes it in GitLab's docs before installing"* — ❌ *"`npx @gitlab/mcp-server`"*. When no official server is known, write the category and the five vetting checks from [`reference.md`](reference.md): publisher, source available, pinned version, tools exposed, and whether it can run code or reach the network beyond its own API.

4. **Grant read-only by default, per stage, not per session.** The scope is the narrowest token scope, one repository or project, one database role on a replica — ✅ *"GitLab token, `read_api`, project `payments-web` only"* — ❌ *"GitLab token with `api`"*. Write access goes **only** to the stage whose output is that write (posting the release, opening the draft merge request), on a **separate credential** from the read one, and is the user's choice to grant; otherwise a person does the write. When the vendor offers no scope narrower than full API access for that write, a person does it. Never grant write to a **verify** or **gate** stage: a review that can merge, approve, close or comment is no longer a review. No admin, owner, org-wide or `*` scopes, ever.

5. **Write what each server must not be able to do.** Name the concrete actions to exclude — merge, approve, push to the default branch, transition or close issues, post to channels, run SQL writes, delete, change settings. "Read-only" alone is not enough when the vendor's read-only mode still exposes a tool the stage doesn't need; list the toolsets to turn off.

6. **Split untrusted reading from write or exec.** Issue text, merge request and PR comments, tickets, chat messages, web pages, log lines and design-file comments are **untrusted input**: anyone who can write there can write instructions. A stage that reads untrusted content and also holds a write tool, a shell, or a network tool is the dangerous combination. Fix it by splitting the stage (one reader that returns a file, one actor that reads only that file), dropping the write to a person, or dropping the server. ✅ *"implement runs tests (exec), so it gets no tracker server; it reads the story file shape wrote, which a person skims first"*.

7. **Cut every server that doesn't earn its attack surface.** A server earns its place when the input is too large, too structured or too live to paste at the stage's cadence: dozens of items (a release's 40 merge requests), fields that matter (a cycle's issues with status and owner), or data that changes by the minute (a live incident). A handful of items fetched weekly or less, or a step that saves a single copy-paste, gets the export file instead. Say which servers were cut and why.

8. **Give every stage its export-file fallback.** Name the file a person produces without a server — the diff saved to a file, the tracker filter exported as CSV, the dashboard panel's data downloaded, the query result saved as CSV — so the loop still runs where no server is allowed.

9. **Place the secrets.** Tokens live in environment variables or the tool's secret store; a committed config file holds variable names, never values. A project-scoped config that contains a token stays out of git. Read and write credentials are separate variables. Point at OAuth where the vendor offers it, so no long-lived token exists.

10. **Emit with [`templates/mcp-pairing.md`](templates/mcp-pairing.md)**: the plan in two or three sentences, the per-stage pairing table (stage, needs, server, grant, must not, fallback, risk), the credential list, servers cut, vetting checks for anything not confirmed official, and "To confirm". When the plan still puts private data, untrusted content and any way to send data out in one session, end with one sentence recommending an exfiltration-path review of the finished setup.

**Non-interactive runs** (subagent, CI, headless): unnamed tools become categories tagged `[assumption]`, unknown cadence is assumed weekly, and unknown writers into a source make it untrusted. If no loop, workflow or task is given at all, emit `BLOCKED: need the loop, workflow or task the servers are for`, then say in plain words that the plan needs its stages and the tools the team uses — a pairing for invented stages pairs nothing.

## Useful references in this skill

- [`reference.md`](reference.md) — stage types and their access ceiling, needs by category with the usual export fallback, the vetting checklist, known vendor read-only controls, the cut rule, and the skilldrop loops' stages
- [`templates/mcp-pairing.md`](templates/mcp-pairing.md) — output skeleton
- [`examples/build-loop-github-jira-datadog.md`](examples/build-loop-github-jira-datadog.md) — worked example: the build loop for a team on GitHub, Jira and Datadog; two read-only servers, one optional write credential, Datadog cut

## Quality bar

- **Every stage has a row,** including the ones that get **None**. A plan that lists only servers hides which stages hold nothing.
- **No verify or gate stage holds a write scope.** Not comment, not approve, not label.
- **Every write grant names the stage whose output it is** and sits on its own credential.
- **No invented names.** Every server, package, URL and scope in the plan came from the user or is a vendor's own server with the confirm step written beside it.
- **Every grant is narrower than "read-only":** a scope, a project or repository, a role.
- **Every stage that reads untrusted content is checked** against write, exec and network tools in the same session, and the combination is split or dropped.
- **Every stage has an export-file fallback** a person can produce today.
- **At least one server is argued against** or the plan says why each one earns its place.
- **No token value appears anywhere,** and the config placement keeps tokens out of git.

## When to use this skill

- ✅ "Which MCP servers should we hook up for our release loop?"
- ✅ Wiring a tracker, repo host, chat, observability tool or database into a loop or recurring agent workflow
- ✅ Deciding token scopes, project limits and database roles for an agent's servers, stage by stage
- ✅ Tightening an existing MCP config that grew one server and one wide token at a time

## When NOT to use this skill

- ❌ Threat-modelling a finished agent's tools and data for exfiltration paths — `agent-threat-model`
- ❌ Designing the loop itself: stages, exit criteria, caps, human gates — `agent-loop-design`
- ❌ Deciding how to split work across subagents and what each one is told — `subagent-design`
- ❌ Writing the organization's rules for which AI tools and data are allowed — `ai-usage-policy`
- ❌ Setting up one tracker step by step (Jira, Linear, GitHub Projects) — that is the per-tracker integration guide in the skilldrop docs, not a plan

## Anti-patterns to avoid

- ❌ **One session-wide token for the whole loop.** The verify stage then holds the implement stage's write scope.
- ❌ **A review stage that posts its own comments or merges.** The verdict goes to a person or to CI; the reviewer holds read only.
- ❌ **Inventing the server.** `@vendor/mcp-server` written from memory is how a typosquatted package gets installed with a production token.
- ❌ **"Read-only, so safe."** Read-only stops writes to the vendor; it does nothing about untrusted text steering a stage that has a shell.
- ❌ **Connecting everything the team uses.** A monthly report does not need a live Slack server with history across every channel.
- ❌ **A token in `.mcp.json`.** Committed files hold `${VAR}` references, never values.
- ❌ **Admin scope "to get it working".** A 403 means the scope is wrong for that tool; widen to the one permission named in the error, on that stage's credential only.
- ❌ **Showing the machinery.** Don't mention this skill, its files or its steps in the reply.
- ❌ **A bare `BLOCKED` line.** Keep it, then say in plain words what is missing and what the plan will contain.
