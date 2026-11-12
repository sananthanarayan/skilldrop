"""Nightly invoice run entry point."""

from ledgerline.db import direct_connection
from ledgerline.scheduler.lock import invoice_run_lock
from ledgerline.invoicing import run_nightly


def main():
    with direct_connection() as conn, invoice_run_lock(conn) as acquired:
        if not acquired:
            print("another worker holds the invoice-run lock; exiting")
            return
        run_nightly()


if __name__ == "__main__":
    main()
