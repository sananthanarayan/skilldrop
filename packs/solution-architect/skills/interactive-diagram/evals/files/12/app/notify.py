import logging

import requests
import yaml

from app import db

_cfg = yaml.safe_load(open("config.yaml"))
log = logging.getLogger(__name__)


def send_ready(hold_id):
    row = db.one(
        "SELECT h.id, p.id AS patron_id, p.contact_pref, t.title "
        "FROM holds h JOIN patrons p ON p.id = h.patron_id JOIN titles t ON t.id = h.title_id "
        "WHERE h.id = %s",
        (hold_id,),
    )
    payload = {
        "event": "hold.ready",
        "patron_id": row["patron_id"],
        "contact_pref": row["contact_pref"],
        "title": row["title"],
    }
    try:
        requests.post(
            _cfg["notify"]["webhook_url"],
            json=payload,
            timeout=_cfg["notify"]["timeout_seconds"],
        )
    except requests.RequestException:
        log.warning("hold.ready webhook failed for hold %s", hold_id)
