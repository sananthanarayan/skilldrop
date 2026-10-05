# {Project / component} — Setup guide

**Goal:** {one sentence — the end state, e.g. "Run the API locally with a seeded database and answer a request on `localhost:3000`."}
**Time:** ~{N} minutes
**You'll have at the end:** {concrete artifact — "a running server, a seeded DB, and a passing health check"}

## Placeholders used in this guide

Replace these everywhere they appear. Nothing else is a placeholder.

| Placeholder | What to put | Where to get it |
|---|---|---|
| `<YOUR_API_KEY>` | {what it is} | {where to obtain it} |
| `<DB_PASSWORD>` | {what it is} | {…} |

## Prerequisites

Check each before starting — a failed setup is almost always a missing prerequisite.

| Need | Version | Check it | If missing |
|---|---|---|---|
| {Node / Python / Docker / …} | `>= {x.y}` | `node --version` | {install link / command} |
| {…} | … | `…` | … |

## Steps

### 1. {Imperative — e.g. "Clone the repo and enter it"}

```bash
git clone {repo-url} && cd {repo-dir}
```

**You should see:** {what success looks like — e.g. "a `package.json` in the directory: `ls package.json`"}

### 2. {Imperative — e.g. "Install dependencies"}

```bash
{exact command — e.g. `npm ci`}
```

**You should see:** {e.g. "`added 412 packages` with no errors"}

### 3. {Imperative — e.g. "Configure environment"}

```bash
cp .env.example .env
# then set:
#   API_KEY=<YOUR_API_KEY>
#   DB_PASSWORD=<DB_PASSWORD>
```

**You should see:** {e.g. "`.env` exists and has no remaining `<…>` placeholders: `grep '<' .env` returns nothing"}

### 4. {Imperative — e.g. "Start dependencies"}

```bash
{e.g. `docker compose up -d postgres`}
```

**You should see:** {e.g. "`docker compose ps` shows postgres as `healthy`"}

### 5. {Imperative — e.g. "Run migrations and seed"}

```bash
{e.g. `npm run db:migrate && npm run db:seed`}
```

**You should see:** {e.g. "`Migrations complete (3 applied)` and `Seeded 12 rows`"}

### 6. {Imperative — e.g. "Start the service"}

```bash
{e.g. `npm run dev`}
```

**You should see:** {e.g. "`Listening on http://localhost:3000`"}

## Verify it works

One end-to-end check that proves the whole setup, not just the last step.

```bash
{e.g. `curl -s localhost:3000/health`}
```

**Expected:** {e.g. `{"status":"ok","db":"connected"}`}

If you get this, you're done.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| {exact error text} | {what's actually wrong} | {command or step to fix} |
| `ECONNREFUSED ...:5432` | Postgres not up yet | Re-run step 4; wait for `healthy` |
| {…} | … | … |

## Teardown

```bash
{e.g. `docker compose down -v`}
```

Removes {what — "containers and the local volume; your `.env` is left intact"}.

## Next steps

- {Where to go now — "Run the test suite: `npm test`"}
- {Link to the design walkthrough or API reference for this project, if one exists}
