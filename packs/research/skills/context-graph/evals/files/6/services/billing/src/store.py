"""Billing persistence: in-place updates to the Postgres invoice ledger."""

LEDGER_TABLE = "invoices_ledger"


def record_charge(conn, invoice_id, amount_minor):
    conn.execute(
        f"UPDATE {LEDGER_TABLE} SET balance_minor = balance_minor + %s WHERE invoice_id = %s",
        (amount_minor, invoice_id),
    )
