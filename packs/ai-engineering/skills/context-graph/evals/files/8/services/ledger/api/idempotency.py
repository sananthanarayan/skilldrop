import json
from datetime import timedelta

KEY_TTL = timedelta(hours=24)


def lookup(conn, key: str):
    row = conn.execute(
        "SELECT response FROM idempotency_keys WHERE key = %s AND created_at > now() - %s",
        (key, KEY_TTL),
    ).fetchone()
    return json.loads(row[0]) if row else None


def store(conn, key: str, response: dict) -> None:
    conn.execute(
        "INSERT INTO idempotency_keys (key, response) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (key, json.dumps(response)),
    )
