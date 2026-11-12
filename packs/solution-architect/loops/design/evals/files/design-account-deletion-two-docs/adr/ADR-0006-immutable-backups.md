# ADR-0006: Nightly backups are immutable for 35 days

Relates to: ADR-0002
Status: Accepted

## Context
After a ransomware scare at a partner club platform, we want backups an attacker with
production credentials cannot alter.

## Decision
The Postgres cluster is backed up nightly to write-once storage. Each backup is kept for
35 days and then expires automatically. No one, including us, can edit or delete an
individual backup or the records inside it before it expires.

## Consequences
Strong protection against tampering. Any record deleted from production still exists in
backups until the last backup containing it expires. A restore brings back whatever the
backup held.

## Alternatives considered
Mutable backups with restricted access; rejected as too easy to tamper with.
