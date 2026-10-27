import random
import time

MAX_ATTEMPTS = 3
BASE_DELAY_SECONDS = 1
MAX_DELAY_SECONDS = 30


def with_retry(fn):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return fn()
        except Exception:
            if attempt == MAX_ATTEMPTS:
                raise
            cap = min(MAX_DELAY_SECONDS, BASE_DELAY_SECONDS * 2 ** (attempt - 1))
            time.sleep(random.uniform(0, cap))
