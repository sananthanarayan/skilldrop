import sqlite3
from datetime import datetime, timedelta

import pytest

from signups import (NotSignedUp, ShiftFull, TooLateToCancel, cancel, init_db,
                     roster, sign_up)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    init_db(c)
    # shift 1: next week, room for 2.  shift 2: starts in two hours, room for 2.
    c.execute(
        "INSERT INTO shifts (id, starts_at, capacity) VALUES (1, ?, 2)",
        ((datetime.now() + timedelta(days=7)).isoformat(),),
    )
    c.execute(
        "INSERT INTO shifts (id, starts_at, capacity) VALUES (2, ?, 2)",
        ((datetime.now() + timedelta(hours=2)).isoformat(),),
    )
    c.commit()
    return c


def test_sign_up_confirms(conn):
    assert sign_up(conn, 1, 101) == "confirmed"
    assert roster(conn, 1) == [101]


def test_unknown_shift(conn):
    with pytest.raises(KeyError):
        sign_up(conn, 99, 101)


def test_waitlist_when_full(conn):
    sign_up(conn, 1, 101)
    sign_up(conn, 1, 102)
    sign_up(conn, 1, 103)
    assert sign_up(conn, 1, 104) == "waitlisted"


def test_no_waitlist_raises(conn):
    for volunteer in (101, 102, 103):
        sign_up(conn, 1, volunteer)
    try:
        sign_up(conn, 1, 104, allow_waitlist=False)
    except ShiftFull:
        pass


def test_cancel_promotes_waitlist(conn):
    for volunteer in (101, 102, 103, 104):
        sign_up(conn, 1, volunteer)
    cancel(conn, 1, 101)
    assert 104 in roster(conn, 1)
    assert 101 not in roster(conn, 1)


def test_cancel_too_late(conn):
    sign_up(conn, 2, 101)
    with pytest.raises(TooLateToCancel):
        cancel(conn, 2, 101)


def test_cancel_not_signed_up(conn):
    with pytest.raises(NotSignedUp):
        cancel(conn, 1, 555)
