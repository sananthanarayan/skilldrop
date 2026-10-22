"""Idempotency claims in Redis (see ADR-0003)."""
from src.redis_client import redis

TTL_SECONDS = 24 * 3600


def claim(event_id, partner_id) -> bool:
    return bool(redis.set(f"idem:{event_id}:{partner_id}", 1, nx=True, ex=TTL_SECONDS))
