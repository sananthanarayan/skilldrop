"""Read-through price cache (RFC-012)."""
import json

from shopfront.redis_client import redis
from shopfront.settings import load_yaml
from shopfront.pricing.client import fetch_price

TTL = load_yaml("config/cache.yaml")["pricing"]["ttl_seconds"]


def get_price(sku: str) -> dict:
    key = f"price:{sku}"
    hit = redis.get(key)
    if hit is not None:
        return json.loads(hit)
    price = fetch_price(sku)
    redis.set(key, json.dumps(price), ex=TTL)
    return price


def touch(sku: str, ttl: int) -> None:
    redis.expire(f"price:{sku}", ttl)
