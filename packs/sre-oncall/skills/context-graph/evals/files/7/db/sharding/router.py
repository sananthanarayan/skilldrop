"""Pick the shard for a tenant (DD-006)."""

import hashlib

SHARD_COUNT = 16


def shard_for(tenant_id: str) -> int:
    return int(hashlib.sha256(tenant_id.encode()).hexdigest(), 16) % SHARD_COUNT
