# Worked example: a cache breakpoint that "didn't move the bill"

Input → output oracle for `prompt-caching-advisor`. Shows a breakpoint that never caches
because its prefix is under the minimum size, a per-customer block that splits a shared cache
in two, and the fix as a reordering, not an extra marker.

## Input

> Our support bot runs on Haiku. We added `cache_control` to the instructions block because
> that's the static part, and the input bill didn't move. Should we add another one on the
> catalogue? Numbers: about 150,000 requests a day, conversations average 6 turns with a turn
> every 1–2 minutes, busy all day and quiet overnight. The catalogue is rebuilt once a night
> at 02:00.

```python
def build_request(customer, session, question):
    system = [
        {"type": "text", "text": INSTRUCTIONS,                # ~3,200 characters
         "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": render_profile(customer)},   # ~1,400 characters, per customer
        {"type": "text", "text": load_catalogue()},           # ~62,000 characters
    ]
    messages = session.history + [{"role": "user", "content": question}]
    return {"model": MODEL, "max_tokens": 800, "system": system, "messages": messages}
```

## Output

**Don't add a second marker yet. Fix the order first.** Two things are wrong, and a marker on
the catalogue in its current position would only fix half of it.

1. **Your current breakpoint caches nothing.** A breakpoint caches the whole prefix up to and
   including its block. Here that is the instructions alone: 3,200 characters, or about 800
   tokens. Haiku's minimum is about 1,024 tokens, so the API processes it as normal input,
   with no error and no saving. That is why the bill didn't move.
2. **The customer profile sits in front of the catalogue.** The profile differs for every
   customer, so any breakpoint after it makes a separate cache entry per customer. A marker
   on the catalogue where it sits now would cache instructions + profile + catalogue together.
   It would hit only on later turns of the same conversation, and every customer's first turn
   would pay to write 16,600 tokens to the cache.

Move the catalogue above the profile, put one breakpoint at the end of the catalogue, and put
a second, moving breakpoint on the latest user turn.

### Annotated structure

| Block | Size (~4 chars/token) | Class | Cached by |
|---|---|---|---|
| Instructions | 3,200 ch ≈ 800 tok | Static | BP1 (as part of its prefix) |
| Catalogue | 62,000 ch ≈ 15,500 tok | Static until the 02:00 rebuild | BP1 |
| Customer profile | 1,400 ch ≈ 350 tok | Quasi-static (per conversation) | BP2 |
| Earlier turns | grows each turn | Fixed once sent | BP2 |
| Latest question | varies | Dynamic | written by BP2 for the *next* turn to read |

```python
def build_request(customer, session, question):
    system = [
        # Static. ~800 tokens: under Haiku's ~1,024 minimum, so no marker of its own.
        # It is still cached, because BP1's prefix includes it.
        {"type": "text", "text": INSTRUCTIONS},
        # Static until the 02:00 rebuild. ~15,500 tokens.
        {"type": "text", "text": load_catalogue(),
         "cache_control": {"type": "ephemeral"}},   # BP1: instructions + catalogue, ~16,300 tokens,
                                                    # identical for every customer
        # Quasi-static: the same for a whole conversation, different per customer.
        # It sits after BP1 so it can't split the shared entry.
        {"type": "text", "text": render_profile(customer)},
    ]
    latest = {
        "role": "user",
        "content": [{"type": "text", "text": question,
                     "cache_control": {"type": "ephemeral"}}],  # BP2: profile + all earlier turns + this one
    }
    # session.history stores turns WITHOUT cache_control. If the marker is saved into history,
    # markers pile up turn after turn, and from turn 4 the request carries more than the API's
    # limit of four breakpoints.
    messages = session.history + [latest]
    return {"model": MODEL, "max_tokens": 800, "system": system, "messages": messages}
```

BP2 is not caching dynamic content. It writes the conversation so far, so that the next turn,
where this question is now fixed history, can read it. Nothing that changes between requests
sits in front of BP1, and that is the prefix every customer shares.

Two breakpoints, one per logical boundary: content shared by everyone, then content shared
within a conversation. A third marker on the instructions would add nothing, because they are
under the minimum and already inside BP1's prefix.

### Cache strategy summary

BP1 caches the instructions and catalogue, about 16,300 tokens, as one entry shared by every
customer. At about 150,000 requests a day it stays warm all through the busy hours, so its hit
rate is near 100%. It misses on the first request after the 02:00 rebuild and after any
overnight gap longer than the cache's five-minute lifetime. BP2 caches each conversation's
profile and earlier turns. With turns 1–2 minutes apart, turns 2–6 read it, about 5 of 6
requests. Before the change, about 16,600 tokens of instructions, profile and catalogue were
processed at full price on every request, roughly 2.5 billion input tokens a day. After it,
almost all of that is a cache read, billed at about a tenth of the normal input price. The
largest costs left are output tokens and each turn's new question. This answer gives no dollar
figure: the request didn't include prices, and the hit rates above are estimates until the
response `usage` fields (`cache_read_input_tokens`, `cache_creation_input_tokens`) confirm
them.

## Why this is the oracle

- **The last block caches everything before it.** The user's mental model, "mark the static
  block", is per block. A breakpoint marks a prefix. That one rule explains why the
  instructions marker did nothing (its prefix is 800 tokens) and why a catalogue marker in
  the current order would be keyed per customer (its prefix includes the profile).
- **Check the size before recommending a cache.** The fix removes the user's existing marker,
  because it is under Haiku's minimum. The instructions still get cached, inside BP1.
- **Never let dynamic or per-user content split a shared prefix.** The profile is not dynamic
  per request, but it is per customer. Moving it below BP1 turns a per-conversation cache into
  a shared one. The comment on `session.history` heads off the four-breakpoint error that a
  moving breakpoint causes when it is stored.

A cheaper pass answers the question as asked: "Yes, add `cache_control` to the catalogue
block." That gives each conversation a cache entry of its own, a premium cache write on every
first turn, and a bill that drops far less than expected. The team blames caching, and the
dead instructions marker stays in the code.
