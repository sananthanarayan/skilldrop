# RFC-012: One retry policy for every service

Status: Accepted
Date: 2025-03-18
Authors: Teodora Basu
Governs: services/*/retry.py

Each service had invented its own retry rules, which made incident timelines hard to
read. Every service's `retry.py` uses the same policy: at most 3 attempts in total,
full-jitter exponential backoff with a 1 second base and a 30 second cap.
