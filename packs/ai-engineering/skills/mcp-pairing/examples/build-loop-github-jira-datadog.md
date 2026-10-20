# Worked example — the build loop on GitHub, Jira and Datadog

## Input given to the skill

> We're adopting the build loop for the `orders-api` repo. We use GitHub for code and PRs,
> Jira (project ORD) for stories and bugs, and Datadog for logs and APM. Which MCP servers
> should we connect, and with what access? We'd like the agent to open the PR itself if that's
> sensible. About one bug a week needs logs; stories come in daily. Outside contractors open
> PRs too.

---

# MCP pairing — build loop for `orders-api`

**Tools in use:** GitHub, Jira (project ORD), Datadog · **Assumptions:** the developer's
checkout is local, so implement needs no repo server `[assumption]`; Jira issues in ORD are
written by staff and by people raising bugs from support `[assumption]`.

## The plan

Connect two servers, both read-only: Jira for the shape stage and GitHub for the verify stage.
Implement and decide need none. Datadog is cut: one bug a week is a saved log query, not a live
server. Opening the PR is the one write worth granting, on its own GitHub credential used only
at the end of implement, and only if the team wants it; otherwise the developer opens the PR.

## Pairing by stage

| Stage (type, cadence) | Needs | Server | Grant | Must not | Fallback without it | Risk |
|---|---|---|---|---|---|---|
| shape (generate, daily) | Tracker issue: the story or bug, its comments and links | Atlassian's own server — confirm Atlassian publishes it in Atlassian's docs before connecting | A Jira account with Browse on project ORD only; the server acts with that account's permissions | Create, transition, comment, assign, edit fields; see any project but ORD | The issue exported from Jira to a text file, or the filter exported as CSV | Issue text and comments are untrusted (support-raised bugs). Shape holds no write or exec tool, so reading them is safe here; it writes the story file and nothing else |
| shape, bugs only (generate, ~weekly) | Logs and traces for the failing request | Cut — see below | — | — | The Datadog log query result saved as JSON, and the trace's spans exported, for the bug's time window | Log lines carry request fields an attacker writes; a file a person picked keeps that bounded |
| implement (generate, per story) | None — works from the story file shape wrote and the local checkout | None | — | — | — | Implement runs tests (exec) and edits files (write), so it gets **no** tracker or GitHub server: live issue text next to a shell is the dangerous combination. A person skims the story file before implement starts |
| implement → open PR (generate, per story, optional) | Action: open a draft PR from the pushed branch | GitHub's own server, write configuration — confirm GitHub publishes it (GitHub's own organization, docs on GitHub's domain) | A separate fine-grained token, `orders-api` only: Pull requests read and write, Contents read and write; branch protection on `main` requires review | Merge, approve, push to `main`, change settings or branch protection, touch other repositories | The developer runs the push and opens the PR by hand | Write and exec in one stage, so this stage reads nothing untrusted: no issue comments, no PR comments |
| verify (verify, per PR) | Repo: the PR diff, description, CI status | GitHub's own server in its read-only mode, limited to the repositories, pull requests and Actions toolsets | A separate fine-grained token, `orders-api` only: Contents read, Pull requests read, Actions read | Merge, approve, comment, request changes, label, re-run CI | The diff saved as a `.diff` file and the PR description copied to a file; the CI summary saved | Contractor PRs and comments are untrusted, and the gate script is exec. Allow only the gate script command in this session; the verdict goes to a person, never posted by the agent |
| decide (gate, per PR) | None — reads verify's verdict and any design disagreement | None | — | — | — | The merge stays a person's action in GitHub's own UI under their own login |

## Credentials

| Variable | Server | Scope | Used by stages | Kind |
|---|---|---|---|---|
| None — OAuth sign-in, no stored token | Atlassian | Browse, project ORD | shape | Read |
| `GH_ORDERS_READ` | GitHub | Contents, Pull requests, Actions: read; `orders-api` | verify | Read |
| `GH_ORDERS_PR_WRITE` | GitHub | Pull requests and Contents: read and write; `orders-api` | implement → open PR (optional) | Write, separate token |

Tokens live in environment variables or the client's secret store. The project's committed MCP
config holds variable names only. The write server is a separate server entry, enabled only in
the session that opens the PR, so the verify session never loads it.

## Servers cut

- **Datadog** — needed for about one bug a week. A saved log query and exported trace cover it,
  with no standing token to the team's logs and no live attacker-written log lines in context.
  Revisit if bugs needing logs reach several a week.

## Check before installing

- **Atlassian's own server** — confirm publisher; it acts with the account's own permissions,
  so the account must have nothing beyond Browse on ORD.
- **GitHub's own server** — confirm publisher, use its read-only mode for verify, and turn off
  every toolset verify doesn't use.

## To confirm

- Whether the team wants the agent to open PRs at all; if not, drop `GH_ORDERS_PR_WRITE`.
- That branch protection on `main` requires an approving review, so even the write token cannot
  land code alone.

Next step: review the finished setup for any path where issue or PR text could make the agent
send private data out, before the first real story runs through it.
