"""Signed, stateless session cookies (ADR-0007)."""

COOKIE_MAX_AGE_SECONDS = 8 * 60 * 60


def read_cookie(raw_cookie, signing_key):
    raise NotImplementedError
