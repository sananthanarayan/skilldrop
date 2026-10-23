"""Retry failed email and SMS sends (RFC-0005)."""

INTERVAL_S = 300
GIVE_UP_AFTER_S = 24 * 60 * 60
