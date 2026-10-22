"""Single-runner guard for the nightly invoice run (ADR-0007)."""

from contextlib import contextmanager

INVOICE_RUN_LOCK_KEY = 727001


@contextmanager
def invoice_run_lock(conn):
    """Hold a session-level advisory lock for the duration of the run.

    `conn` must be a dedicated, direct connection (not via PgBouncer transaction pooling).
    Yields True if this process holds the lock, False if another worker already does.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s)", (INVOICE_RUN_LOCK_KEY,))
        acquired = cur.fetchone()[0]
    try:
        yield acquired
    finally:
        if acquired:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(%s)", (INVOICE_RUN_LOCK_KEY,))
