"""Volunteer shift sign-ups for the Harbourside Food Bank scheduling app."""
import sqlite3
from datetime import datetime, timedelta, timezone

CANCEL_CUTOFF_HOURS = 24

SCHEMA = """
CREATE TABLE IF NOT EXISTS shifts (
    id INTEGER PRIMARY KEY,
    starts_at TEXT NOT NULL,      -- ISO 8601, stored in UTC
    capacity INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS signups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shift_id INTEGER NOT NULL REFERENCES shifts(id),
    volunteer_id INTEGER NOT NULL,
    status TEXT NOT NULL,         -- 'confirmed' | 'waitlisted' | 'cancelled'
    created_at TEXT NOT NULL
);
"""


class ShiftFull(Exception):
    pass


class TooLateToCancel(Exception):
    pass


class NotSignedUp(Exception):
    pass


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def _confirmed_count(conn: sqlite3.Connection, shift_id: int) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM signups WHERE shift_id = ? AND status = 'confirmed'",
        (shift_id,),
    ).fetchone()
    return row[0]


def sign_up(conn: sqlite3.Connection, shift_id: int, volunteer_id: int,
            allow_waitlist: bool = True) -> str:
    """Sign a volunteer up for a shift. Returns 'confirmed' or 'waitlisted'."""
    shift = conn.execute(
        "SELECT capacity FROM shifts WHERE id = ?", (shift_id,)
    ).fetchone()
    if shift is None:
        raise KeyError(f"no shift {shift_id}")
    capacity = shift[0]

    if _confirmed_count(conn, shift_id) > capacity:
        if not allow_waitlist:
            raise ShiftFull(f"shift {shift_id} is full")
        status = "waitlisted"
    else:
        status = "confirmed"

    conn.execute(
        "INSERT INTO signups (shift_id, volunteer_id, status, created_at) "
        "VALUES (?, ?, ?, ?)",
        (shift_id, volunteer_id, status, datetime.now().isoformat()),
    )
    conn.commit()
    return status


def cancel(conn: sqlite3.Connection, shift_id: int, volunteer_id: int) -> None:
    """Cancel a sign-up. The first volunteer on the waitlist takes the spot."""
    row = conn.execute(
        "SELECT id, status FROM signups "
        "WHERE shift_id = ? AND volunteer_id = ? AND status != 'cancelled'",
        (shift_id, volunteer_id),
    ).fetchone()
    if row is None:
        raise NotSignedUp(f"volunteer {volunteer_id} is not on shift {shift_id}")
    signup_id, status = row

    starts_at = datetime.fromisoformat(
        conn.execute(
            "SELECT starts_at FROM shifts WHERE id = ?", (shift_id,)
        ).fetchone()[0]
    )
    if starts_at - datetime.now() < timedelta(hours=CANCEL_CUTOFF_HOURS):
        raise TooLateToCancel(
            f"cancellations close {CANCEL_CUTOFF_HOURS}h before the shift"
        )

    conn.execute("UPDATE signups SET status = 'cancelled' WHERE id = ?", (signup_id,))

    if status == "confirmed":
        nxt = conn.execute(
            "SELECT id FROM signups WHERE shift_id = ? AND status = 'waitlisted' "
            "ORDER BY created_at DESC LIMIT 1",
            (shift_id,),
        ).fetchone()
        if nxt is not None:
            conn.execute(
                "UPDATE signups SET status = 'confirmed' WHERE id = ?", (nxt[0],)
            )
    conn.commit()


def roster(conn: sqlite3.Connection, shift_id: int) -> list[int]:
    """Volunteer ids confirmed for a shift, in sign-up order."""
    rows = conn.execute(
        "SELECT volunteer_id FROM signups "
        "WHERE shift_id = ? AND status = 'confirmed' ORDER BY id",
        (shift_id,),
    ).fetchall()
    return [r[0] for r in rows]
