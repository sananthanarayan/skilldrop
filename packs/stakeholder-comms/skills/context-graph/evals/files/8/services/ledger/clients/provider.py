import random
import time

import httpx
import yaml

with open("config/http.yaml") as fh:
    _cfg = yaml.safe_load(fh)["provider"]


def _sleep(attempt: int) -> None:
    base = _cfg["backoff"]["base_ms"] / 1000
    time.sleep(random.uniform(0, base * (2 ** attempt)))


def call(method: str, path: str, **kwargs) -> httpx.Response:
    retries = _cfg["max_retries"] if method in _cfg["retry_methods"] else 0
    for attempt in range(retries + 1):
        try:
            resp = httpx.request(
                method,
                _cfg["base_url"] + path,
                timeout=_cfg["timeout_seconds"],
                headers={"Authorization": f"Bearer {_cfg['api_key']}"},
                **kwargs,
            )
            if resp.status_code not in (502, 503):
                return resp
        except httpx.TransportError:
            if attempt == retries:
                raise
        _sleep(attempt)
    return resp
