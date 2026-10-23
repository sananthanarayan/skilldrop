"""Delivery attempt log (see ADR-0002)."""
from src.db import execute


def record_attempt(event_id, partner_id, attempt_no, status_code):
    execute(
        "INSERT INTO delivery_attempts (event_id, partner_id, attempt_no, status_code, sent_at) "
        "VALUES (%s, %s, %s, %s, now())",
        (event_id, partner_id, attempt_no, status_code),
    )


def mark_failed(event_id, partner_id):
    execute(
        "UPDATE delivery_attempts SET final_status = 'failed' "
        "WHERE event_id = %s AND partner_id = %s",
        (event_id, partner_id),
    )
