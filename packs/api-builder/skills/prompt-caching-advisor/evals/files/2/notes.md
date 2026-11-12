# Calder Tutor: usage and the caching ask

- About 1,800 students and 60 instructors use the tutor.
- A typical session is 12 turns, with a turn every 1 to 3 minutes. Sessions are spread through the
  day; there are long gaps overnight.
- The handbook changes once per term. The few-shot examples have not changed since launch.
- Our dev lead's plan: put a cache_control breakpoint on every block — the user line, the
  handbook, the few-shot examples, the tools, the case study, and every user turn — "so nothing is
  ever reprocessed".
- Finance wants the exact monthly saving from caching before we ship it.
