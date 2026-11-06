import datetime
import os

import psycopg2
import psycopg2.extras

_conn = psycopg2.connect(os.environ["DATABASE_URL"])


def _cur():
    return _conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def query(sql, params=()):
    with _cur() as c:
        c.execute(sql, params)
        return c.fetchall()


def one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    with _cur() as c:
        c.execute(sql, params)
    _conn.commit()


def insert(sql, params=()):
    with _cur() as c:
        c.execute(sql, params)
        new_id = c.fetchone()["id"]
    _conn.commit()
    return new_id


def today():
    return datetime.date.today()
