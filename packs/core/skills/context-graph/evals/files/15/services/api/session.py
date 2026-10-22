"""Dispatcher sessions for services/api (ADR 9): signed, encrypted cookies, no server store."""
import os
import time

from itsdangerous import URLSafeTimedSerializer

SECRET = os.environ.get("SESSION_SECRET", "placeholder-not-a-real-secret")
MAX_AGE_SECONDS = 8 * 3600
_serializer = URLSafeTimedSerializer(SECRET, salt="haulmark-session")


def issue(user_id: str, role: str) -> str:
    return _serializer.dumps({"uid": user_id, "role": role, "iat": int(time.time())})


def read(cookie: str):
    return _serializer.loads(cookie, max_age=MAX_AGE_SECONDS)
