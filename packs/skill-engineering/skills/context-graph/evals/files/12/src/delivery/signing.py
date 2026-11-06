"""HMAC-SHA256 signing of webhook bodies."""
import hashlib
import hmac
import time

from src.secrets import partner_secret


def sign(partner, body: bytes) -> dict:
    ts = str(int(time.time()))
    msg = ts.encode() + b"." + body
    digest = hmac.new(partner_secret(partner["id"]), msg, hashlib.sha256).hexdigest()
    return {"X-Parcelhook-Signature": digest, "X-Parcelhook-Timestamp": ts}
