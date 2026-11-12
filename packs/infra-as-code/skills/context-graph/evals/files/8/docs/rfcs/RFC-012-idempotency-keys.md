# RFC-012: Idempotency keys for posting entries

- **State:** Draft
- **Author:** j.lindqvist
- **Opened:** 2025-08-02

## Summary

Clients send an `Idempotency-Key` with every `PostEntry` call. The ledger stores the key and
the response for 24 hours and returns the stored response on a repeat.

## Proposed implementation

`services/ledger/api/idempotency.py`, backed by a table `idempotency_keys` in PostgreSQL.

## Open questions

- Is 24 hours long enough for the batch importer, which can retry after a day?
- Should a key reused with a different body be a 409 or a 422?
