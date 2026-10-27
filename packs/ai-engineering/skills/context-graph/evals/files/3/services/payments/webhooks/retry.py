"""Webhook retry policy (RFC-0006)."""

FIRST_DELAY_S = 2
MAX_DELAY_S = 600
MAX_ATTEMPTS = 8


def should_retry(status_code, attempt):
    if attempt >= MAX_ATTEMPTS:
        return False
    return status_code == 429 or status_code >= 500


def delay_for(attempt):
    return min(FIRST_DELAY_S * 2 ** attempt, MAX_DELAY_S)
