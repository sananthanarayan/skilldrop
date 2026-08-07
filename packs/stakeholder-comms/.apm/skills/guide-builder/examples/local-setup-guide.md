# Example: raw notes → setup guide

Shows the two things that make this skill earn its keep: the **style-detection call up front**, and the **verify-after-every-step** discipline that turns notes into something a stranger can follow.

---

## Input (what the user pasted)

> need a getting-started doc for `widget-api`. it's a Go service, needs Postgres 15. clone, copy the env file (need a STRIPE_KEY from the dashboard), `make deps`, bring up postgres with docker, `make migrate`, then `make run`. it serves on 8080. there's a `/healthz`. people keep forgetting to start postgres first and then complain migrate hangs.

## The skill's first line back (style detection)

> Reading this as a **setup guide** — it's clone → configure → run with a defined finish line (`/healthz` answering). Two things I'm filling with defaults; correct me if wrong: end state is **running locally** (not deployed), and the prerequisite baseline assumes Go and Docker are already installed. Drafting now.

## Output

---

# widget-api — Setup guide

**Goal:** Run `widget-api` locally against a Dockerized Postgres and get a healthy response from `/healthz`.
**Time:** ~10 minutes
**You'll have at the end:** the API serving on `localhost:8080` with migrations applied.

## Placeholders used in this guide

| Placeholder | What to put | Where to get it |
|---|---|---|
| `<STRIPE_KEY>` | Stripe secret key for the test mode | Stripe Dashboard → Developers → API keys |

## Prerequisites

| Need | Version | Check it | If missing |
|---|---|---|---|
| Go | `>= 1.22` | `go version` | https://go.dev/dl |
| Docker | any recent | `docker --version` | https://docs.docker.com/get-docker |
| Postgres image | 15 | (pulled in step 3) | — |

## Steps

### 1. Clone the repo and enter it

```bash
git clone git@github.com:example/widget-api.git && cd widget-api
```

**You should see:** a `Makefile` in the directory — `ls Makefile`.

### 2. Configure environment

```bash
cp .env.example .env
# then set in .env:
#   STRIPE_KEY=<STRIPE_KEY>
```

**You should see:** no placeholders left — `grep '<' .env` returns nothing.

### 3. Start Postgres (do this before migrating)

```bash
docker compose up -d postgres
```

**You should see:** `docker compose ps` lists `postgres` as `healthy`. Wait for `healthy` before the next step — migrating against a not-yet-ready Postgres is what makes `make migrate` appear to hang.

### 4. Install Go dependencies

```bash
make deps
```

**You should see:** `go mod download` completes with no errors.

### 5. Run migrations

```bash
make migrate
```

**You should see:** `migrations applied: N` and a return to the prompt within a few seconds.

### 6. Start the service

```bash
make run
```

**You should see:** `widget-api listening on :8080`.

## Verify it works

```bash
curl -s localhost:8080/healthz
```

**Expected:** `{"status":"ok","db":"connected"}`

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `make migrate` hangs | Postgres not `healthy` yet | Re-check step 3; wait for `healthy`, then retry |
| `connection refused :5432` | Postgres container not up | `docker compose up -d postgres` |
| `/healthz` returns `db:"down"` | migrations not applied | run step 5 |

## Teardown

```bash
docker compose down -v
```

Removes the Postgres container and its volume. Your `.env` is left intact.

## Next steps

- Run the tests: `make test`
- Reference for the endpoints this service exposes: generate one with `/guide-builder` in **API reference** style.

---

### Why this passes the quality bar

- **Every step ends in a check** — the reader never guesses whether to continue.
- **The one gotcha from the notes** ("people forget to start postgres") became step 3's check *and* the first troubleshooting row, instead of buried prose.
- **The single placeholder is listed once up front**, not left as a surprise mid-command.
- **One end-to-end verify** (`/healthz`) proves the whole chain, not just the last command.
