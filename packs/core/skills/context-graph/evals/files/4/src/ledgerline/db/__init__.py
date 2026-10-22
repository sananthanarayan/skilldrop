"""Postgres access (ADR-0002)."""

import os
from contextlib import contextmanager

import psycopg

# DATABASE_URL goes through PgBouncer (transaction pooling); DATABASE_DIRECT_URL does not.
POOLED_URL = os.environ.get("DATABASE_URL", "postgresql://app:CHANGE_ME@pgbouncer:6432/ledgerline")
DIRECT_URL = os.environ.get("DATABASE_DIRECT_URL", "postgresql://app:CHANGE_ME@db:5432/ledgerline")


@contextmanager
def pooled_connection():
    with psycopg.connect(POOLED_URL) as conn:
        yield conn


@contextmanager
def direct_connection():
    with psycopg.connect(DIRECT_URL, autocommit=True) as conn:
        yield conn
