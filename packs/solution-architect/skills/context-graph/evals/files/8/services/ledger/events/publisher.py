import json

import yaml
from confluent_kafka import Producer

from services.ledger.logging import get_logger

log = get_logger(__name__)

with open("config/messaging.yaml") as fh:
    _cfg = yaml.safe_load(fh)

_producer = Producer({
    "bootstrap.servers": ",".join(_cfg["bootstrap_servers"]),
    "acks": _cfg["acks"],
})


def publish_entry_posted(entry) -> None:
    payload = {
        "type": "EntryPosted",
        "entry_id": entry.id,
        "account_id": entry.account_id,
        "amount_minor": entry.amount_minor,
        "currency": entry.currency,
    }
    _producer.produce(_cfg["topic"], key=entry.account_id, value=json.dumps(payload))
    log.info("event published", extra={"account_id": entry.account_id})
