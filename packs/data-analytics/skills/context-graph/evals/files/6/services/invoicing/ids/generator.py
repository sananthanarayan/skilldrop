"""Invoice ID generation."""

from libs.money.ulid import new_ulid


def new_invoice_id():
    return f"INV-{new_ulid()}"
