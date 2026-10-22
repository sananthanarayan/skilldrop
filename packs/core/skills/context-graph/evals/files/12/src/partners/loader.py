"""Load partner configuration."""
import time

from src.db import execute

_cache = {"at": 0, "partners": []}
RELOAD_SECONDS = 60


def load_partners():
    if time.time() - _cache["at"] > RELOAD_SECONDS:
        rows = execute("SELECT id, url, events FROM partners WHERE enabled")
        _cache["partners"] = [{"id": r[0], "url": r[1], "events": r[2]} for r in rows]
        _cache["at"] = time.time()
    return _cache["partners"]
