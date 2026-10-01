"""Tiny shared client for the Figma REST API.

Used by the other scripts in this directory. Not meant to be run directly.
"""

from __future__ import annotations

import os
import re
import sys
import time
from typing import Any

import requests

API_BASE = "https://api.figma.com"
FILE_KEY_RE = re.compile(r"figma\.com/(?:file|design|board)/([A-Za-z0-9]+)/")


def token() -> str:
    tok = os.environ.get("FIGMA_TOKEN")
    if not tok:
        sys.stderr.write(
            "error: FIGMA_TOKEN is not set.\n"
            "  Get one at: Figma → Settings → Security → Personal access tokens\n"
            "  Then: export FIGMA_TOKEN=figd_...\n"
        )
        sys.exit(2)
    return tok


def extract_file_key(arg: str) -> str:
    """Accept either a Figma URL or a bare file key."""
    m = FILE_KEY_RE.search(arg)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9]+", arg):
        return arg
    sys.stderr.write(f"error: could not extract a Figma file key from {arg!r}\n")
    sys.exit(2)


def _request(method: str, path: str, **kwargs: Any) -> requests.Response:
    headers = kwargs.pop("headers", {})
    headers["X-Figma-Token"] = token()
    url = f"{API_BASE}{path}"
    for attempt in range(3):
        resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
        if resp.status_code == 429:
            retry = int(resp.headers.get("Retry-After", "2"))
            sys.stderr.write(f"rate-limited, sleeping {retry}s\n")
            time.sleep(retry)
            continue
        return resp
    return resp  # last response, even if 429


def get(path: str, **kwargs: Any) -> dict[str, Any]:
    resp = _request("GET", path, **kwargs)
    if not resp.ok:
        sys.stderr.write(f"error: GET {path} → {resp.status_code} {resp.text[:200]}\n")
        sys.exit(1)
    return resp.json()


def post(path: str, json: dict[str, Any]) -> dict[str, Any]:
    resp = _request("POST", path, json=json)
    if not resp.ok:
        sys.stderr.write(f"error: POST {path} → {resp.status_code} {resp.text[:200]}\n")
        sys.exit(1)
    return resp.json()
