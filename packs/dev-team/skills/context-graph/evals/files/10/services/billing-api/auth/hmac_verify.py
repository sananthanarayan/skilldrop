"""Verify the X-Tallow-Signature header on internal requests (see ADR-0004)."""
import hashlib
import hmac
import os
import time
from functools import wraps

from flask import abort, request

MAX_SKEW_SECONDS = 300


def _shared_key() -> bytes:
    # Shared with ledger-worker.
    return os.environ["BILLING_LEDGER_HMAC_KEY"].encode()


def require_hmac_signature(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        ts = request.headers.get("X-Tallow-Timestamp", "0")
        sig = request.headers.get("X-Tallow-Signature", "")
        if abs(time.time() - int(ts)) > MAX_SKEW_SECONDS:
            abort(401)
        msg = f"{request.method}\n{request.path}\n{ts}\n".encode() + request.get_data()
        expected = hmac.new(_shared_key(), msg, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            abort(401)
        return view(*args, **kwargs)

    return wrapper
