# Rollout plan — {change name}

**{Two lines: the answer to the user's question, the input fact that settles it, and the shape of the plan.}**
✅ *"No: at 2,000 users an hour a 1% step needs about 20 days to see a 0.3 pp error rise, so Tuesday-to-Friday proves nothing. Run internal for a day, 10% for 3 days, 50% for a day, and reach 100% the Wednesday after."*

**Binding constraint:** {the fact that paces the plan: a partner cap, a billing or batch cycle, a deadline, the segments the flag can target, a shadow run, or volume. "None: traffic is high, the default ladder applies."}
**Flag:** `{key}`, evaluated {server / client / edge}, targets by {user / account / tenant / %} · **Assumptions:** {one line, each tagged `[assumption]`}

## Ladder

| Step | Dates | Who is in it, and why | Judged on | Promote when |
|---|---|---|---|---|
| 0 | {Mon 7 Sep – Tue 8 Sep} | {internal / test accounts: crashes at no customer cost} | crashes only | {no abort for 24 h} |
| 1 | {…} | {named cohort or `hash(salt + id) mod 100 < 10`; why these; who is held back} | {units or cycle this step sees, in one phrase} | {every threshold below holds at the step's end} |
| 2 | {…} | | | |
| {n} | {date} | everyone | {holdback or the last comparison} | — |

{One sentence of arithmetic, with its inputs: what the smallest useful step is and why.}
{Deadline line when there is one: ✅ *"100% on 14 Sep, 9 days before the deadline; one failed cycle misses it."*}

## Thresholds

All compare the flag-on cohort with the flag-off cohort over the same window. Counts, not
percentages, where a step sees fewer than about 100 of the unit.

| Metric | Baseline | Promote if | Abort (any time, {automatic / manual}) |
|---|---|---|---|
| {decision metric} | {from input} | {≤ control + 0.3 pp / zero unexplained} | {> 3× control for 5 min → flag off} |
| {guardrail} | | | |

- **Hold:** {sample short or metric between threshold and abort → extend once by {time or cycle}, then roll back}.
- **Watcher:** {role} · **Sign-off before each promotion:** {role, if one is needed} · **Override:** {one role, reason written down}.

## What turning the flag off does not undo

Flag off: {who}, takes effect in {seconds / cache TTL / next app launch}. Only rows this change touches:

| What | Undone? | Handling |
|---|---|---|
| {messages sent / money moved / records written in a new format / third-party records} | no | {correction or reissue path, reversal procedure, what keeps reading the new format} |

**Point of no return:** {the step and why / none}.

## Flag removal

**Owner:** {name from the input, else role} · **Date:** {date} · **Gate:** {100% for 14 days or one full cycle, no rollback} · **Removes:** `{key}`, the old path, its config and dashboards · **Keeps:** {any reader the old records need}.

## To confirm

- {at most 4 facts, each one that would change a step}
