"""Minimal Anthropic Messages API client — stdlib only, so CI needs no pip install.

Used by run_evals.py (weekly eval run) and run_skill.py (the GitHub Action). Retries the
statuses the API documents as transient (429 rate limit, 529 overloaded, 5xx) with backoff,
honouring a retry-after header when one is sent.
"""
import json
import os
import time
import urllib.error
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
RETRY_STATUS = {429, 500, 502, 503, 504, 529}


class APIError(RuntimeError):
    pass


def api_key():
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()


def messages(model, system, user, max_tokens=1024, cache_system=False, retries=4, timeout=180, raw=False):
    """One user turn; returns (text, usage). cache_system marks the system prompt cacheable,
    which pays off when the same long system prompt is sent many times in a row. raw=True
    returns (text, response) instead, for callers that need the served model or stop_reason."""
    key = api_key()
    if not key:
        raise APIError("ANTHROPIC_API_KEY is not set")
    sys_block = {"type": "text", "text": system}
    if cache_system:
        sys_block["cache_control"] = {"type": "ephemeral"}
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "system": [sys_block],
        "messages": [{"role": "user", "content": user}],
    }).encode()
    headers = {"x-api-key": key, "anthropic-version": API_VERSION, "content-type": "application/json"}
    for attempt in range(retries + 1):
        req = urllib.request.Request(API_URL, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.load(r)
            text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
            return text, (data if raw else data.get("usage", {}))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf8", "replace")[:300]
            if e.code in RETRY_STATUS and attempt < retries:
                wait = float(e.headers.get("retry-after") or 2 ** (attempt + 1))
                time.sleep(min(wait, 60))
                continue
            raise APIError(f"HTTP {e.code}: {detail}") from None
        except urllib.error.URLError as e:
            if attempt < retries:
                time.sleep(2 ** (attempt + 1))
                continue
            raise APIError(f"network error: {e.reason}") from None
    raise APIError("retries exhausted")
