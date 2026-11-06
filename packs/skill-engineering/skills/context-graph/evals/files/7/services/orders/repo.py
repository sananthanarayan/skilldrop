"""Orders persistence. SQL lives in db/queries/orders.sql."""

from pathlib import Path

QUERIES = Path(__file__).resolve().parents[2] / "db" / "queries" / "orders.sql"


def load_queries():
    return QUERIES.read_text()
