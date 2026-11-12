# 6. Archive delivered shipments to object storage

Date: 2022-03-14

## Status

Accepted

## Context

`haulmark_core` has grown to 900 GB, most of it shipments delivered more
than a year ago that are only read for audits.

## Decision

A nightly job in `services/archiver/` moves shipments delivered more than
90 days ago out of `haulmark_core` into S3-compatible object storage as
Parquet files, one file per depot per day, and deletes them from PostgreSQL.

## Consequences

`haulmark_core` stays small. Audit queries over archived shipments go
through the object store, not the shipments API.
