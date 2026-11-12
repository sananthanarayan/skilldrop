# ADR-0005: Media store for member photos

Relates to: ADR-0002
Status: Accepted

## Context
Photos are too large to keep in Postgres rows.

## Decision
Member and club photos are stored as objects in the media store at media.stridewell.example.
Postgres holds only the object key. Objects are private and served through short-lived
signed URLs. Deleting an object is immediate; there is no versioning.

## Consequences
Postgres stays small. The app must delete the object as well as the key, or the photo
is orphaned.

## Alternatives considered
Storing photos in Postgres as bytea; rejected for size.
