# 004. Cache the product catalogue in process

- Status: Accepted
- Date: 2024-02-27

## Context

Catalogue reads are about 70% of API traffic, and the catalogue changes a few times a day.

## Decision

Each app container holds the catalogue in an in-process LRU cache (`lru-cache`, 5,000 items,
10-minute TTL) in `src/catalog/cache.ts`. We deliberately do **not** put the catalogue in
Redis: it adds a network hop to the hottest path for data that is fine to be a few minutes
stale per container.

## Consequences

Containers may briefly disagree after a catalogue update. That is acceptable.
