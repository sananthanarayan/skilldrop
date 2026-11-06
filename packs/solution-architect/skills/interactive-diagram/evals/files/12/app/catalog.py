import json

import redis
import yaml

from app import db

_cfg = yaml.safe_load(open("config.yaml"))
_cache = redis.Redis.from_url(_cfg["redis"]["url"])
_TTL = _cfg["redis"]["search_ttl_seconds"]


def search(q):
    key = f"search:{q.lower()}"
    hit = _cache.get(key)
    if hit:
        return json.loads(hit)
    rows = db.query(
        "SELECT id, title, author FROM titles WHERE title ILIKE %s LIMIT 50",
        (f"%{q}%",),
    )
    _cache.setex(key, _TTL, json.dumps(rows))
    return rows
