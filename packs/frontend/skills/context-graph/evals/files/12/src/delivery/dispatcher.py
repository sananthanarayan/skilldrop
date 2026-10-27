"""Consume tracking events and deliver them to partner endpoints."""
import json
import urllib.request

from src.idempotency import redis_store
from src.partners.loader import load_partners
from src.delivery.signing import sign
from src.delivery.retry import schedule_retry
from src.store.delivery_log import record_attempt


def dispatch(event, attempt_no=1):
    for partner in load_partners():
        if event["type"] not in partner["events"]:
            continue
        # drop duplicates from the at-least-once feed
        if not redis_store.claim(event["id"], partner["id"]):
            continue
        body = json.dumps(event).encode()
        headers = {"Content-Type": "application/json", **sign(partner, body)}
        req = urllib.request.Request(partner["url"], data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
        except Exception:
            status = 0
        record_attempt(event["id"], partner["id"], attempt_no, status)
        if not 200 <= status < 300:
            schedule_retry(event, partner, attempt_no)
