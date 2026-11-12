from __future__ import annotations

import time

import structlog_tiny

log = structlog_tiny.get_logger(__name__)

MAX_ATTEMPTS = 3


def fetch_with_retry(client, url: str):
    """Fetch ``url``, retrying on timeout.

    quillstream's ``Client.fetch`` returns ``None`` when the request times out.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = client.fetch(url)
        if result is None:
            log.warning("quillstream fetch timed out", url=url, attempt=attempt)
            time.sleep(2 ** attempt)
            continue
        return result
    raise RuntimeError(f"gave up fetching {url} after {MAX_ATTEMPTS} attempts")
