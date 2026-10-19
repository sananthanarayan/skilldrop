"""Nightly: charge a daily fine on every overdue loan, capped per loan."""
import yaml

from app import db

_cfg = yaml.safe_load(open("config.yaml"))
RATE = _cfg["fines"]["daily_rate_pence"]
CAP = _cfg["fines"]["cap_pence"]


def run():
    overdue = db.query(
        "SELECT id, patron_id, due_date FROM loans WHERE returned_at IS NULL AND due_date < current_date"
    )
    for loan in overdue:
        days = (db.today() - loan["due_date"]).days
        amount = min(days * RATE, CAP)
        db.execute(
            "INSERT INTO fines (loan_id, patron_id, amount_pence) VALUES (%s, %s, %s) "
            "ON CONFLICT (loan_id) DO UPDATE SET amount_pence = EXCLUDED.amount_pence",
            (loan["id"], loan["patron_id"], amount),
        )


if __name__ == "__main__":
    run()
