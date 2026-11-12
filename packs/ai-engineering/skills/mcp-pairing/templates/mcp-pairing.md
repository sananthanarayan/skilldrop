# MCP pairing — {loop, workflow or task}

**Tools in use:** {only the tools the user named} · **Assumptions:** {each tagged [assumption]}

## The plan

{Two or three sentences: connect N servers, which ones, read or write; which stages need none;
which server was cut and why.}

## Pairing by stage

| Stage (type, cadence) | Needs | Server | Grant | Must not | Fallback without it | Risk |
|---|---|---|---|---|---|---|
| {stage} ({generate / verify / gate}, {per change / daily / weekly / monthly}) | {category of context or action} | {server the user named, or "{vendor}'s own server, confirm {how}", or the category + vetting} | {scope, one project / repo / role} | {merge, comment, transition, post, write SQL…} | {the export file a person produces} | {untrusted content read; write, exec or network held; what to split} |
| {stage} | None — works from {previous stage's output} | None | — | — | — | — |

## Credentials

| Variable | Server | Scope | Used by stages | Kind |
|---|---|---|---|---|
| {NAME_READ} | {server} | {scope, project} | {stages} | Read |
| {NAME_WRITE} | {server} | {scope, project} | {the one stage whose output is the write} | Write, separate token |

Tokens live in {environment variables / the client's secret store}. Committed config holds
variable names only; {any project file that holds a value} stays out of git.

## Servers cut

- **{server or category}** — {cadence and why the export file wins}.

## Check before installing

For each server not confirmed as the vendor's own: publisher, source available, pinned version
or commit, tools it exposes (turn off the rest), and whether it can run code or reach the
network beyond its own API.

- **{server}** — {which checks are still open}

## To confirm

- {each fact the plan needs and the input didn't give}

{One plain sentence on the next step, e.g. reviewing the finished setup for ways data could be sent out.}
