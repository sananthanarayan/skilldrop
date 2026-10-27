"""Minimal ULID helper (placeholder implementation for the fixture)."""

import os
import time


def new_ulid():
    return f"{int(time.time() * 1000):012x}{os.urandom(10).hex()}"
