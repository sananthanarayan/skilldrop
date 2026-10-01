---
name: prompt-caching-advisor
description: Analyzes a prompt or conversation structure and identifies the highest-value cache breakpoints — where to insert cache_control checkpoints to minimize repeated token processing. Use when designing or optimizing a Claude API integration that uses prompt caching, when input costs are dominated by a static system prompt or few-shot block, or when a multi-turn conversation reprocesses the same context on every turn.
---

# prompt-caching-advisor

Identifies where to place `cache_control` checkpoints in a Claude API prompt or conversation structure to minimize repeated token processing. The savings are real — a cache hit on a 10,000-token system prompt costs ~90% less than re-processing it — but the placement matters. Wrong breakpoints waste the minimum cacheable block size or cache dynamic content that never hits.

## How to respond

### Step 1 — Understand the structure

Ask the user to share (or describe) their prompt structure. You need:
- The system prompt (or a description of what's in it and roughly how long)
- Any few-shot examples passed in messages
- The shape of the variable user turn (what changes per request)
- Whether this is single-turn or multi-turn

If they share code, read the messages array. The cache breakpoint goes at the end of the block you want cached — a `cache_control: {"type": "ephemeral"}` on the **last content block** of a message causes everything up to and including that block to be cached.

### Step 2 — Classify each block

For each distinct block, classify it:

| Class | Characteristics | Cache? |
|---|---|---|
| **Static** | Same on every request (system instructions, reference docs, few-shot examples) | Yes — put breakpoint at the end |
| **Quasi-static** | Same for a session or user, different across users (user profile, project context) | Yes, with session-scope awareness |
| **Dynamic** | Changes every request (current user message, real-time data, timestamps) | No — never cache |

### Step 3 — Recommend breakpoints

State exactly where to place each `cache_control` checkpoint. Show the code:

```python
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "<static few-shot examples here>",
                "cache_control": {"type": "ephemeral"}  # breakpoint 1 — caches system + examples
            },
            {
                "type": "text",
                "text": user_query  # dynamic — no cache_control
            }
        ]
    }
]
```

For system prompts, the cache breakpoint goes on the last block of the system array.

### Step 4 — Estimate cache hit rate

Give a rough hit rate estimate:
- **Near 100%**: static system prompt, fixed few-shot examples, no dynamic injection into the cached block
- **~session %**: user-context cached per-session; hits on turn 2+, misses on first turn per user
- **Low**: anything that embeds timestamps, UUIDs, or per-request data in the cached block

### Step 5 — Warn on sub-threshold blocks

Warn if a block the user wants to cache is likely under the minimum cacheable size:
- **Haiku**: ~1,024 tokens minimum
- **Sonnet / Opus**: ~2,048 tokens minimum

A block under the minimum is processed as normal — no error, just no cache savings. Calculate roughly: 1 token ≈ 4 characters of English prose. A 2,000-character system prompt (~500 tokens) won't benefit on Sonnet/Opus.

### Step 6 — Output format

Produce:
1. **Annotated structure** — show the messages array with `cache_control` placements marked and commented
2. **Cache strategy summary** — one paragraph: what is cached, why, expected hit rate, and the dominant cost driver before and after

## Anti-patterns

- **Caching dynamic content.** If a user query, timestamp, or per-request database result is inside a cached block, every request is a cache miss — the structure defeats itself. Identify and flag before recommending.
- **Recommending a cache on a block under the minimum size.** A 300-token block doesn't cache on Sonnet/Opus. The API doesn't error — it just processes normally. Always check size before recommending.
- **Recommending four or more breakpoints.** More than three breakpoints on a single request is almost always a sign the prompt structure should be simplified, not patched with caches.

Use `token-budget-estimator` after this skill if the user also wants to size the token budget across components.

## Quality bar

- **Never cache dynamic content.** A user query, a timestamp, a database result retrieved per-request — these must not appear in a cached block. If the user's structure embeds dynamic content in an otherwise static block, flag it before recommending the cache.
- **One breakpoint per logical boundary.** A system prompt with three sections (instructions, reference docs, examples) can have up to three breakpoints. More than four breakpoints on a single request is a signal the structure needs rethinking.
- **The last block caches everything before it.** This is the most common misunderstanding — the cache breakpoint is not a marker for just that block, it's a marker for the entire prefix up to that point.
