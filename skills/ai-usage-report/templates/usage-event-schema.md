# usage-event-schema

Input to `ai-usage-report` is a CSV or JSONL file. Each row / each JSON object is one **usage event** — a single invocation of an AI tool or skill by a single user.

## Required fields

| Field | Type | Notes |
|---|---|---|
| `timestamp` | ISO 8601 datetime | e.g. `2026-05-21T14:32:11Z` |
| `user` | string | Stable identifier — email, handle, or employee ID. Use the same value for the same person across events. |
| `tool` | string | What was invoked — e.g. `claude-code`, `cursor`, `copilot`, or a specific skill name like `deck-builder` |

If any of these three is missing, the script exits with an error. They are the minimum needed to compute a volume report.

## Optional but recommended fields

| Field | Type | Used for |
|---|---|---|
| `session_id` | string | Groups events into sessions. Needed for **session depth** and **single-shot rate**. |
| `output_consumed` | bool / `0` / `1` / `true` / `false` | Whether the AI output ended up in a shipped artifact. Needed for **effectiveness rate**. |
| `consumed_at` | ISO 8601 datetime | When the output landed in the shipped artifact. Needed for **output-to-shipped lag**. |
| `output_size` | int | Tokens or characters of AI output |
| `prompt_size` | int | Tokens or characters of the user prompt (do **not** include the prompt text itself — see privacy note below) |
| `outcome` | enum: `success` / `error` / `cancelled` | Filter for errors that distort volume |

## Fields the skill explicitly does NOT want

- ❌ **The prompt text.** Prompts contain code, customer data, and personal context. The skill works from metadata only.
- ❌ **The output text.** Same reason.
- ❌ **Free-form user notes** about their session. Redact before passing to the skill.

If your telemetry source captures these, drop them at export time — not after the report is generated.

## Graceful degradation

The script reads what's there and labels missing-signal columns explicitly. The signal-to-field mapping:

| If your input has… | …the report can show |
|---|---|
| Just the 3 required fields | Volume + breadth |
| `+ session_id` | …and session depth + single-shot rate |
| `+ output_consumed` | …and effectiveness rate + AI-theater flag column |
| `+ consumed_at` | …and output-to-shipped lag |
| `+ outcome` | …and an error-filtered version of every metric |

When a column is omitted, the report includes a *"Where signals are missing"* section listing exactly which optional fields were absent and which metrics consequently couldn't be computed. This is the contract: the report never lies about what it knows.

## Example: CSV

```csv
timestamp,user,tool,session_id,output_consumed,consumed_at,outcome
2026-05-21T09:14:23Z,alice@acme.com,claude-code,sess-001,1,2026-05-21T11:02:00Z,success
2026-05-21T09:14:55Z,alice@acme.com,claude-code,sess-001,1,2026-05-21T11:02:00Z,success
2026-05-21T09:18:02Z,alice@acme.com,deck-builder,sess-001,1,2026-05-21T14:30:00Z,success
2026-05-21T10:01:11Z,bob@acme.com,cursor,sess-014,0,,success
2026-05-21T10:01:30Z,bob@acme.com,cursor,sess-014,0,,success
2026-05-21T14:22:08Z,carol@acme.com,claude-code,sess-029,1,2026-05-22T08:11:00Z,success
```

## Example: JSONL

```jsonl
{"timestamp": "2026-05-21T09:14:23Z", "user": "alice@acme.com", "tool": "claude-code", "session_id": "sess-001", "output_consumed": true, "outcome": "success"}
{"timestamp": "2026-05-21T09:14:55Z", "user": "alice@acme.com", "tool": "claude-code", "session_id": "sess-001", "output_consumed": true, "outcome": "success"}
{"timestamp": "2026-05-21T10:01:11Z", "user": "bob@acme.com", "tool": "cursor", "session_id": "sess-014", "output_consumed": false, "outcome": "success"}
```

## A note on the `output_consumed` signal

This is the field that matters most for the effective-vs-performative distinction. It's also the hardest one to populate accurately. Three common implementations, ranked by signal quality:

1. **Diff-based attribution** (best): the telemetry source tracks whether AI output text appears (or fuzzy-matches) in a subsequent commit / PR / doc within N hours. High signal, hard to game.
2. **Explicit accept/reject events** (good): the IDE emits "user accepted the suggestion" vs "user rejected it." Medium signal — accepting and then immediately deleting still counts as consumed.
3. **Self-reported** (weakest): the user checks a box "did you use this?" Low signal — captures intent but easy to game and high reporting burden.

If your telemetry source uses (3), don't pretend the resulting effectiveness rate is more reliable than it is. The report can still be useful for spotting outliers, but the numbers should be read with that grain of salt.
