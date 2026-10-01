from booking.app import health


def test_health():
    assert health() == {"ok": True}
