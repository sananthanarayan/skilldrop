# ADR-0002: Postgres is the system of record

Relates to: ADR-0001
Status: Accepted

## Context
We run one team and one on-call rota. Every extra datastore is another thing to back up,
patch and page on.

## Decision
All application data lives in the single Postgres cluster. Adding any new datastore
(cache, search index, key-value store, document store) needs an ADR that supersedes or
amends this one.

## Consequences
One backup and restore path. Some workloads are less efficient than on a specialised store.

## Alternatives considered
A document store for run logs; rejected for the extra operational load.
