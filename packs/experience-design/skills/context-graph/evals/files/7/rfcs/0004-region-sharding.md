# RFC 0004: Shard by region instead of tenant

Status: Withdrawn
Date: 2025-02-14
Author: P. Tamboli
Supersedes: DD-006
Governs: db/sharding/

## Proposal
Move from tenant sharding to region sharding (eu, us, apac) so data-residency rules map to shards.

## Withdrawal note (2025-03-20)
Withdrawn after the cost review: re-sharding every tenant was estimated at two quarters of work and
residency can be met by pinning tenants to regional shards under the existing scheme. Tenant
sharding (DD-006) stays.
