# AI Usage Telemetry — design doc

> Companion to the `ai-usage-report` skill in skilldrop. This doc covers the *collection* side: what an MCP server (or any telemetry pipeline) needs to log so the report skill has signal to work with. It is the spec for a separate repo, not for skilldrop.

## Goals

- Capture AI usage events from the IDEs / tools developers actually use (Claude Code, Cursor, Copilot, ChatGPT, internal Claude API apps).
- Capture *enough downstream signal* to distinguish "AI output landed in something shipped" from "AI output was generated and abandoned."
- Make the per-event payload small, the schema stable, and the privacy posture explicit.
- Expose the data via an MCP server so report-generators (skilldrop's `ai-usage-report`, dashboards, ad-hoc queries) can consume it.

## Non-goals

- **Not** an AI grading system. The data surfaces patterns; humans interpret them.
- **Not** real-time content inspection. We log metadata; the prompt and output text never leave the user's device.
- **Not** a replacement for IDE-level telemetry the vendor already collects (GitHub for Copilot, Anthropic for Claude Code). This is a *unified* layer across tools.
- **Not** a productivity-measurement system. Volume metrics are *adoption* signals, not output-quality signals.

## Event schema (the contract)

The schema is the load-bearing piece — the report skill consumes it, the MCP server emits it, the IDEs / tools populate it. Keep it stable.

### Required fields

```json
{
  "timestamp": "2026-05-21T14:32:11Z",
  "user": "alice@acme.com",
  "tool": "claude-code"
}
```

| Field | Type | Notes |
|---|---|---|
| `timestamp` | ISO 8601 | UTC, second precision is enough |
| `user` | string | Stable identifier; email or employee ID. Hash if the org doesn't want raw emails in storage. |
| `tool` | string | `claude-code`, `cursor`, `copilot`, `chatgpt`, `internal-app:<name>`, or a skill name |

### Recommended fields (ship these unless there's a reason not to)

| Field | Type | Notes |
|---|---|---|
| `session_id` | string | Groups events into sessions (a single Claude Code conversation, a Cursor edit session, etc.) |
| `output_consumed` | bool | See "Classification heuristics" below |
| `consumed_at` | ISO 8601 | When the output landed in a shipped artifact (commit, PR, doc) |
| `output_size` | int | Tokens or chars |
| `prompt_size` | int | Tokens or chars (the text itself is **not** sent) |
| `outcome` | enum: `success` / `error` / `cancelled` | Filter for errors |

### Fields explicitly excluded

- The prompt text
- The output text
- File paths beyond the repo level
- Any customer data referenced in the prompt

These never leave the device. If your collector needs them transiently to compute consumption (e.g. diff matching), do it locally and ship only the boolean.

## Additional metrics worth tracking (gap analysis on v1 schema)

The v1 schema above is the *minimum* to produce a useful adoption report. The fields below significantly expand what questions the data can answer. Add them when you can populate them honestly — partial fields (some events have them, others don't) are fine as long as downstream reports degrade gracefully.

### Cost & model

| Field | Type | What it unlocks |
|---|---|---|
| `model` | string | Per-model effectiveness comparison (Opus vs Sonnet vs Haiku, Claude vs GPT-4 vs Copilot). Without this, you can't answer "is the team using the right model for the task?" |
| `provider` | enum: `anthropic` / `openai` / `github` / `cursor` / etc. | Multi-vendor cost rollups |
| `tokens_input` / `tokens_output` | int | Cost calculation; also a proxy for prompt depth |
| `cost_usd` | float | Direct cost per invocation (pre-computed if the vendor exposes it; otherwise derive from token counts × model price) |

**Why this is the biggest gap in v1.** Without `model`, every effectiveness number is averaged across whatever the user happens to be running. A team migrating from Sonnet to Opus looks identical to a team using both arbitrarily.

### Engagement depth

| Field | Type | What it unlocks |
|---|---|---|
| `tool_call_count` | int | For agentic tools (Claude Code, Cursor agents), the number of internal tool calls (Bash, Read, Edit, etc.) inside one invocation. Distinguishes "one-shot Q&A" from "deep agent loop." |
| `iteration_count` | int | Turns within the session before the user moved on |
| `regenerations` | int | Explicit "try again" actions (separate from natural follow-up prompts) |

**Why this matters.** The current `single_shot_rate` metric only counts session length, not depth. A 1-event session with 30 internal tool calls is very different from a 1-event session with one tool call.

### Output quality (beyond binary consumed)

| Field | Type | What it unlocks |
|---|---|---|
| `output_edit_distance` | int or float | Token-level edit distance between the AI output and what actually shipped. Captures "kept but heavily rewritten" — a 5% edit-distance ship is very different from a 90% edit-distance "I rewrote it all" ship. |
| `output_retention_days` | int | Was the AI's contribution still in the codebase N days later? Computed by a periodic sweep. |
| `regeneration_followed` | bool | Did the user regenerate immediately after this invocation? If yes, this output was implicitly judged insufficient. |
| `output_consumed_source` | enum: `diff-attribution` / `accept-event` / `self-reported` | Which heuristic populated `output_consumed`. Same metric can mean very different things by source — surface it. |

### Latency & UX

| Field | Type | What it unlocks |
|---|---|---|
| `latency_ms` | int | Total wait time. Slow AI isn't useful even if outputs are good. |
| `time_to_first_token_ms` | int | Streaming UX signal |
| `interrupted` | bool | User cancelled mid-response (different from `outcome: cancelled` which is API-level) |

### Errors & friction

| Field | Type | What it unlocks |
|---|---|---|
| `error_type` | enum: `rate_limit` / `safety_filter` / `tool_error` / `network` / `quota` | Diagnose adoption blockers — a rash of `rate_limit` errors means the team's hitting plan caps |
| `permission_prompts_count` | int | Claude-Code-specific friction proxy. High counts = users getting interrupted frequently. |

### Context

| Field | Type | What it unlocks |
|---|---|---|
| `task_type` | enum: `bug` / `feature` / `refactor` / `docs` / `test` / `exploration` | Answer "what is AI good at vs bad at?" Either self-tagged by the user, inferred from prompt heuristics, or backfilled from commit message keywords. |
| `language` | string | Python / TS / Go / etc. — different languages show very different AI effectiveness |
| `repo` | string | Per-codebase adoption views; useful for orgs with many repos |

### Downstream outcome (the big one)

| Field | Type | What it unlocks |
|---|---|---|
| `pr_id` / `commit_sha` | string | Linkage from the AI invocation to the artifact it became part of |
| `pr_merged` | bool | Did the AI-assisted PR actually ship? |
| `pr_review_iterations` | int | How many review rounds before merge? High counts on AI-assisted code = "AI got us 80% but reviewers had to do real work." |
| `tests_passed_on_ai_diff` | bool | At merge time, did CI pass on the AI-touched diff? |
| `reverted_within_n_days` | bool | Did the AI-touched code get reverted within 30 days? **Strongest negative outcome signal** — a high revert rate means the AI is shipping plausible code that doesn't survive. |
| `bugs_filed_against_ai_change` | int | Bugs filed against files touched by AI-assisted commits within N days |

**These are the metrics that turn adoption tracking into outcome tracking.** v1 of the schema answers "are people using AI?" — these fields answer "is AI actually helping the org ship better software?" They require a backfill daemon that watches the team's PR/issue tracker, not just IDE events.

### Implementing additional fields

The collector and report can both handle a growing schema gracefully:

- **Collector side**: every additional field is optional. If a particular vendor or tool can't populate it, the field is absent. Don't reject events for missing optional fields.
- **Storage side**: SQLite/Postgres accept NULL columns. Don't make additional fields NOT NULL.
- **Report side**: the report skill already follows the "omit columns with insufficient signal" pattern. Extending it to handle the new fields is mostly adding aggregation logic, not changing the contract.

### What NOT to track

Resist the urge to capture:

- ❌ **Sentiment / "did you find this helpful?" inline buttons** — high reporting burden, low signal, creates survey fatigue
- ❌ **Keystroke- or screen-level activity** — surveillance-tier, will be opposed
- ❌ **The actual prompt text "for context"** — privacy-violating; once it's in the store, you're responsible for everything in there
- ❌ **"Productivity scores" combining multiple metrics into one number** — fake precision, hides the signal you actually need

## Classification heuristics — populating `output_consumed`

This is the hard problem. Three approaches, ranked.

### 1. Diff-based attribution (best signal)

- After each AI invocation, the collector records a fingerprint of the AI output (hash of normalized tokens, or a short n-gram set).
- A daemon watches `git` activity. When the user commits, the collector compares each AI output fingerprint against the committed diff.
- If overlap > threshold (say 30% of AI output tokens appear in the commit, or fuzzy match passes), mark `output_consumed: true` and record `consumed_at`.

**Pros:** High signal, hard to game.
**Cons:** Requires git daemon, fingerprint storage, fuzzy-match tuning. Doesn't catch outputs that landed in non-git artifacts (Notion, Slack, design docs).

### 2. Explicit accept/reject events (good signal)

- The IDE/tool emits "user accepted the suggestion" / "user rejected it" events alongside invocations.
- `output_consumed` = accept event recorded within N minutes of the invocation.

**Pros:** Direct, low-overhead.
**Cons:** Accepting and then deleting still counts as consumed. Not all tools emit these events.

### 3. Self-reported (weakest signal)

- The user is prompted occasionally: "did you use the output of your last AI invocation?"
- Stored as `output_consumed_self_reported: true/false`.

**Pros:** Cheap to implement.
**Cons:** High reporting burden. Easy to game. Most users will skip.

### Recommendation

Ship (1) for git-tracked artifacts. Augment with (2) for IDE-level events when the vendor supports it. Treat (3) as a stop-gap for tools that lack instrumentation, and flag self-reported events distinctly in the schema (`source: "self-reported"`).

The report skill's `output_consumed` rate should be read with awareness of *which heuristic populated it*. If you're running a mix, surface the breakdown.

## MCP server tool surface

Minimum viable tool set the server exposes:

| Tool | Purpose |
|---|---|
| `log_event` | Append a single event to storage. Called by IDE collectors. |
| `query_events` | Read events with filters (`user`, `tool`, `from`, `to`). Returns JSONL. |
| `export_csv` | Same as `query_events` but emits CSV — what feeds `ai-usage-report`. |
| `health` | Liveness; row counts; signal-availability summary. |

Optional but useful:

| Tool | Purpose |
|---|---|
| `register_consumption` | Backfill an `output_consumed` / `consumed_at` event from a diff daemon. |
| `redact_user` | Right-to-be-forgotten: delete all events for a user. |
| `purge_older_than` | Retention policy enforcement. |

## Storage

Three viable choices, depending on scale:

| Scale | Choice | Why |
|---|---|---|
| < 1M events | SQLite | Single file, trivial backup, query with SQL. Good for a team of < 50. |
| 1M – 100M | Postgres | Indexable on `user` + `timestamp`, supports retention policies. |
| > 100M | ClickHouse / DuckDB | Columnar; common for telemetry workloads. |

Default to SQLite. Migrate when you actually need to. Don't pick ClickHouse for 200 events/day.

## Privacy posture (the part that gets you in trouble if you skip)

- **Schema declared up-front**: every field captured is in this doc. No silent additions.
- **Prompts and outputs never leave the device.** Even hashing is local.
- **Per-user opt-out** must be supported. Users who disable telemetry produce zero events; downstream reports show them as `inactive`, not absent.
- **Retention**: default 90 days. Aggregated rollups can be kept longer; raw per-event data should not.
- **Access control**: the `query_events` endpoint requires auth. Per-user-named exports require manager-tier role; team-rollup exports require a lower bar.
- **The data is for adoption insight, not performance review.** This boundary is policy, not technology — write it down, surface it in onboarding, and revisit if managers start asking for it as performance data.
- **Audit**: every `query_events` and `export_csv` call is itself logged (who, when, what filter). The reviewer should expect to be reviewable.

## Open questions / risks

- **Cross-tool identity.** If Alice is `alice@acme.com` in Claude Code and `alice-acme` in Cursor, the report shows two users. Need an identity-mapping table or a canonical resolver.
- **Multi-IDE sessions.** A single task may span Claude Code + manual Cursor edits. `session_id` becomes blurry across tools. Probably accept it and don't try to unify.
- **What counts as a shipped artifact?** Git is easy; Slack, Notion, Figma, decks are not. Either build connectors per surface or accept that effectiveness rates are biased toward git-shippable work.
- **Goodhart's law.** Once teams know `output_consumed` is measured, expect adversarial behavior — pasting AI output into trivial commits to game the metric. The skill flags single-shot + low-effectiveness as a starting place for conversation specifically because the metric will get gamed.
- **Vendor lock vs unified layer.** Anthropic and GitHub each have first-party telemetry. Reconcile this layer against vendor exports rather than duplicating their work.

## Implementation guide — what it takes to actually build this

The earlier draft of this doc had a "2-week build" milestone. Be honest: 2 weeks is enough for the *core server + one collector + stub data*. A version with multiple collectors, real diff attribution, identity resolution, and access control is **4–8 weeks of focused work** for one engineer, longer if parts of it are part-time. This section breaks down what's actually involved.

### Tech-stack recommendation

| Layer | Choice | Why |
|---|---|---|
| Language | **Python 3.11+** | Matches the official MCP Python SDK; easy to share schema code with the skilldrop report skill |
| MCP framework | **`mcp` (Anthropic SDK)** | Official, supports `stdio` and HTTP transports. Alternative: `@modelcontextprotocol/sdk` in TypeScript if your stack is JS. |
| Schema | **`pydantic` v2** | Models double as runtime validation + JSON schema export for documentation |
| Storage (start) | **SQLite (stdlib `sqlite3`)** | Zero-ops; one file; queryable with any SQL tool |
| Storage (grow) | Postgres or DuckDB | Migrate when SQLite locking becomes a bottleneck — usually > 1M events |
| Auth | **Bearer tokens** loaded from env | Don't roll your own session management for an internal tool |
| Tests | **`pytest`** + `pytest-asyncio` | The MCP SDK is async |
| Deploy | **Single container** behind your existing reverse proxy | Don't build a Kubernetes operator for ~10 req/sec |

### Project scaffold

```
ai-usage-telemetry/
├── README.md
├── pyproject.toml
├── docs/
│   ├── schema.md            # Mirror of "Event schema" section
│   ├── privacy.md           # Mirror of "Privacy posture" section
│   └── operators.md         # How to deploy, back up, restore
├── src/ai_usage_telemetry/
│   ├── __init__.py
│   ├── server.py            # MCP server entrypoint
│   ├── schema.py            # Pydantic models for events
│   ├── store/
│   │   ├── sqlite.py        # CRUD + migration runner
│   │   └── migrations/
│   │       └── 001_init.sql
│   ├── tools/
│   │   ├── log_event.py
│   │   ├── query_events.py
│   │   ├── export_csv.py
│   │   ├── register_consumption.py
│   │   └── redact_user.py
│   ├── collectors/
│   │   ├── claude_code/     # Hook scripts + setup docs
│   │   ├── cursor/          # Extension shim
│   │   ├── copilot/         # GitHub export ingester
│   │   └── git_diff_daemon.py
│   ├── identity.py          # Canonical-ID resolver
│   ├── auth.py              # Bearer-token verification
│   └── audit.py             # Audit logger for query/export calls
└── tests/
    ├── test_schema.py
    ├── test_store.py
    ├── test_tools.py
    ├── test_diff_matcher.py
    └── fixtures/             # Synthetic events, fake commits
```

### `pyproject.toml` minimum

```toml
[project]
name = "ai-usage-telemetry"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "mcp>=1.0.0",
  "pydantic>=2.5",
  "click>=8.1",        # For the diff-daemon CLI
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.23", "ruff>=0.5"]

[project.scripts]
ai-telemetry-server = "ai_usage_telemetry.server:main"
ai-telemetry-daemon = "ai_usage_telemetry.collectors.git_diff_daemon:main"
```

### Schema in code

```python
# src/ai_usage_telemetry/schema.py
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal, Optional

class UsageEvent(BaseModel):
    # Required
    timestamp: datetime
    user: str
    tool: str

    # Recommended
    session_id: Optional[str] = None
    output_consumed: Optional[bool] = None
    consumed_at: Optional[datetime] = None
    output_size: Optional[int] = None
    prompt_size: Optional[int] = None
    outcome: Optional[Literal["success", "error", "cancelled"]] = None

    # Cost & model
    model: Optional[str] = None
    provider: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cost_usd: Optional[float] = None

    # Engagement depth
    tool_call_count: Optional[int] = None
    iteration_count: Optional[int] = None
    regenerations: Optional[int] = None

    # ... (additional fields from the gap analysis)
```

### SQLite schema

```sql
-- migrations/001_init.sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,           -- ISO 8601 UTC
    user TEXT NOT NULL,
    tool TEXT NOT NULL,
    session_id TEXT,
    output_consumed INTEGER,           -- 0/1/NULL
    consumed_at TEXT,
    outcome TEXT,
    model TEXT,
    provider TEXT,
    tokens_input INTEGER,
    tokens_output INTEGER,
    -- ... rest of columns
    raw_json TEXT NOT NULL             -- Full event for forward-compat
);
CREATE INDEX idx_events_user_ts ON events(user, timestamp);
CREATE INDEX idx_events_tool_ts ON events(tool, timestamp);
CREATE INDEX idx_events_session  ON events(session_id);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    caller TEXT NOT NULL,              -- who called
    tool TEXT NOT NULL,                -- query_events, export_csv, etc.
    args_json TEXT,                    -- redacted; never includes raw event bodies
    result_count INTEGER
);

CREATE TABLE identity_map (
    canonical_user TEXT NOT NULL,
    alias_user TEXT NOT NULL,
    source TEXT NOT NULL,              -- which tool emits this alias
    PRIMARY KEY (alias_user, source)
);
```

Storing the full event as `raw_json` is a forward-compat trick — schema changes don't lose data. The structured columns are denormalized for query speed.

### MCP server skeleton

```python
# src/ai_usage_telemetry/server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from .schema import UsageEvent
from .store.sqlite import Store
from .auth import require_role

app = Server("ai-usage-telemetry")
store = Store("/var/lib/ai-telemetry/events.db")

@app.tool()
async def log_event(event: dict) -> str:
    """Append a single usage event to the store. Called by IDE collectors."""
    validated = UsageEvent.model_validate(event)
    store.insert(validated)
    return "ok"

@app.tool()
@require_role("reader")
async def query_events(
    user: str | None = None,
    tool: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 1000,
) -> list[dict]:
    """Read events with filters. Returns JSONL-ready dicts."""
    return store.query(user=user, tool=tool, since=since, until=until, limit=limit)

@app.tool()
@require_role("reader")
async def export_csv(
    since: str,
    until: str,
    columns: list[str] | None = None,
) -> str:
    """Emit a CSV ready for the skilldrop ai-usage-report skill."""
    return store.export_csv(since=since, until=until, columns=columns)

def main():
    import asyncio
    asyncio.run(stdio_server(app))

if __name__ == "__main__":
    main()
```

The `@require_role` decorator reads a bearer token from the MCP request context and gates access. Bearer tokens are issued out-of-band (manual; a few users for an internal tool).

### Collectors — the messy part

Collectors are the most varied piece. Each tool needs its own approach. Honest survey:

| Tool | Realistic collection path | Effort |
|---|---|---|
| **Claude Code** | Hooks (`Stop`, `PreToolUse`, `PostToolUse`) in `.claude/settings.json` calling a shell script that POSTs to the MCP server | Low — ~1 day |
| **Cursor** | Custom extension (`vscode-extension` style) that wraps the chat panel and emits events | Medium — 3-5 days |
| **GitHub Copilot** | Vendor doesn't expose per-event hooks for IDE users; use GitHub's *Copilot usage* API for aggregated data instead | Low for org-level; impossible for per-event |
| **Anthropic API direct** | Wrap the SDK in your org with a thin layer that posts events alongside calls | Medium — 2-3 days |
| **ChatGPT (web)** | No reasonable collection path; user-facing — accept it as unobservable | — |

**Claude Code hook example** (collectors/claude_code/setup.md):

```json
// .claude/settings.json on the developer's machine
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "command": "/usr/local/bin/ai-telemetry-emit claude-code stop"
      }
    ]
  }
}
```

The `ai-telemetry-emit` script reads env vars Claude Code exposes (`CLAUDE_SESSION_ID`, etc.) and POSTs a minimal event to the local MCP server.

**Cursor extension** is heavier — you need to publish (or sideload) a VS Code-style extension that subscribes to chat-panel lifecycle events. The official Cursor extension API is the constraint here.

### Diff-attribution daemon — the hard part

This is what makes `output_consumed` meaningful instead of self-reported. Algorithm:

```
1. Subscribe to local git commits (via post-commit hook, fswatch on .git/refs, or polling).
2. For each new commit on a tracked repo:
   a. Get the diff (git diff <prev>..<commit>)
   b. Pull recent fingerprints from the store (last 24 hours, this user)
   c. For each fingerprint, compute overlap with the diff:
      - Normalize whitespace, strip comments
      - Token-set Jaccard or fuzzy n-gram match
   d. If overlap > threshold (start with 30%):
      - Call register_consumption(event_id, commit_sha, consumed_at=now)
3. Periodic backfill: for any fingerprint older than 24h, mark output_consumed=false (it didn't ship).
```

**Subtleties that bite you:**
- Reformatters (prettier, black) destroy literal matches → use AST-level fingerprints for code, not raw text
- Squash-merges erase the per-commit history → also watch PR merge events
- AI-generated code is often "edited and adapted" → 30% overlap threshold catches partial use but creates false positives; tune per-language

This piece alone is 1–2 weeks of work. It's the difference between "we tracked AI usage" and "we tracked AI value."

### Identity resolution

Mapping different per-tool IDs to one canonical person:

```python
# Approach: explicit mapping table, no inference
@app.tool()
@require_role("admin")
async def map_identity(canonical: str, alias: str, source: str) -> str:
    """Register that <alias> from <source> resolves to <canonical>."""
    store.add_identity_mapping(canonical, alias, source)
    return "ok"
```

At query time, all `user` values are resolved through the table before grouping. Aliases without an explicit mapping are treated as their own users (better than wrong attribution).

### Privacy controls — implementation specifics

- **Opt-out**: ship a `disable.sh` script that creates a marker file (`~/.ai-telemetry-disabled`). The hook script reads this and short-circuits before emitting.
- **Right to be forgotten**: implement `redact_user(user)` that deletes all events for that user. Test it; ensure foreign keys (audit log) don't keep stale references.
- **Retention**: cron-based `purge_older_than(days=90)` daily. Test the cron.
- **Audit immutability**: audit_log inserts only; no UPDATE/DELETE in code. Periodic backup to write-once storage if your org needs it.

### Honest phased timeline

| Phase | Duration | Deliverable |
|---|---|---|
| **1. Schema + store + MCP server** | Week 1 | `log_event`, `query_events`, `export_csv` working against SQLite; integration test with synthetic data; one team member can POST events from a curl command |
| **2. First collector (Claude Code)** | Week 2 | Hook-based collector running on 1–2 dev machines; real events arriving in store; ai-usage-report skill consuming the CSV |
| **3. Diff-attribution daemon (basic)** | Week 3 | git post-commit hook → fingerprint match → `register_consumption` calls. Tuned for one language to start. |
| **4. Second collector (Cursor or Anthropic API wrapper)** | Week 4 | Whichever tool the team actually uses most after Claude Code |
| **5. Identity resolution + access control** | Week 5 | Mapping table, role-gated tools, audit log working |
| **6. PR/commit outcome metrics** | Week 6+ | Periodic sweep against the PR API to populate `pr_merged`, `reverted_within_n_days`, etc. |
| **7. Privacy + operational hardening** | Ongoing | Opt-out script, retention cron, backups, on-call docs |

A team that wants to ship "v1, all tools, all metrics" in 2 weeks should expect to ship "v1, one tool, half the metrics." Better to ship the half that works honestly.

### Common failure modes (read before starting)

1. **You ship volume metrics first and nothing else.** Volume is the cheap signal; people read it as effectiveness. Hold the effectiveness work in scope or accept that the project will get judged on the easy numbers.
2. **You skip the diff-attribution daemon because it's hard.** Then `output_consumed` is forever self-reported, and the effectiveness rate is decorative.
3. **You add fields faster than you populate them.** A schema with 25 optional fields where 3 are populated produces reports full of `—`. Limit additions to fields that have a real source.
4. **You let access creep.** Once two managers can query, eventually everyone will. Decide the access model upfront and enforce it in code, not policy.
5. **You let one tool dominate.** If 80% of your events are from Claude Code, the report becomes a Claude Code report. Diversify collection or scope the report to one tool explicitly.

### What to ship to skilldrop from this project

Nothing automatic. The seam between this project and skilldrop is the CSV that `export_csv` produces. Practical contract:

- The CSV columns are a subset of this doc's schema
- skilldrop's `templates/usage-event-schema.md` is the consumer-facing version of this contract
- When this doc's schema changes, update both files in the same PR (one in each repo) and bump the skilldrop skill's manifest version

The two projects stay loosely coupled. Don't import this project's Python from skilldrop, or vice versa.
