"""Nightly export of the delivery log to per-partner S3 prefixes."""
import csv
import io

from src.config import load_yaml
from src.db import execute
from src.s3 import put_object

CFG = load_yaml("config/export.yaml")


def run(day):
    rows = execute(
        "SELECT partner_id, event_id, attempt_no, status_code, sent_at FROM delivery_attempts "
        "WHERE sent_at::date = %s ORDER BY partner_id",
        (day,),
    )
    by_partner = {}
    for r in rows:
        by_partner.setdefault(r[0], []).append(r)
    for partner_id, prows in by_partner.items():
        buf = io.StringIO()
        csv.writer(buf).writerows(prows)
        put_object(CFG["bucket"], f"{partner_id}/{day}.csv", buf.getvalue())
