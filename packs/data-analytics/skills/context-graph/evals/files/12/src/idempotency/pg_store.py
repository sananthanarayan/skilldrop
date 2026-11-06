"""Idempotency claims in Postgres (see ADR-0006)."""
from src.db import execute


def claim(event_id, partner_id) -> bool:
    rows = execute(
        "INSERT INTO idempotency_keys (event_id, partner_id) VALUES (%s, %s) "
        "ON CONFLICT DO NOTHING RETURNING 1",
        (event_id, partner_id),
    )
    return len(rows) == 1
