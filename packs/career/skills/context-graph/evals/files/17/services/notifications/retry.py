import time

MAX_ATTEMPTS = 5
BASE_DELAY_SECONDS = 2


def with_retry(fn):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return fn()
        except Exception:
            if attempt == MAX_ATTEMPTS:
                raise
            time.sleep(BASE_DELAY_SECONDS * 2 ** (attempt - 1))
