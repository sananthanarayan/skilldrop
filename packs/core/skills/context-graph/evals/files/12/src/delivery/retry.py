"""Retry scheduling for failed deliveries."""
from src.config import load_yaml
from src.store.delivery_log import mark_failed
from src.queue import enqueue_delayed

CFG = load_yaml("config/delivery.yaml")["retry"]


def schedule_retry(event, partner, attempt_no):
    if attempt_no >= CFG["max_attempts"]:
        mark_failed(event["id"], partner["id"])
        return
    # TODO(INC-2291): backoff disabled while partner Velo's endpoint flaps; restore afterwards
    delay = CFG["base_delay_seconds"]
    enqueue_delayed(event, partner, attempt_no + 1, delay_seconds=delay)
