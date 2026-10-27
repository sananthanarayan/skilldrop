# RFC-012: Cache prices in Redis

Status: Accepted
Date: 2023-06-14
Author: M. Okafor
Builds on: RFC-008
Governs: shopfront/pricing/cache.py, config/cache.yaml

## Context
The Halvorsen ERP limits `GetItemPrice` to 40 requests/second per client and its p95 latency is
~900 ms. During the June sale the product page timed out and the ERP throttled us for 20 minutes.

## Decision
Put a read-through Redis cache in front of pricing. Key `price:{sku}`, TTL 60 seconds. A price
change in the ERP can therefore take up to a minute to show on the site; merchandising agreed
this is acceptable.

## Alternatives considered
- Nightly price snapshot: rejected, price changes during sales must show within minutes.
- Asking Halvorsen to raise the limit: rejected by the vendor.

## Revisit when
The ERP rate limit no longer applies to us.
