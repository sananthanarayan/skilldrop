# DD-006: Shard by tenant

Status: Accepted
Date: 2023-01-30
Deciders: Platform guild (O. Mensah, R. Vidal)
Governs: db/sharding/

Each tenant's data lives on exactly one shard, chosen by a hash of tenant_id. Cross-tenant queries
go through the reporting replica, never the shards.
