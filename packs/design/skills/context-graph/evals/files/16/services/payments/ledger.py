"""Ledger writes (ADR-0002)."""
import itertools

_ids = itertools.count(1)


def record_payment(merchant_id, body):
    # Real implementation writes payments + ledger_entries in one transaction.
    return {"id": f"pay_{next(_ids)}", "merchant_id": merchant_id, "amount": body["amount"]}
