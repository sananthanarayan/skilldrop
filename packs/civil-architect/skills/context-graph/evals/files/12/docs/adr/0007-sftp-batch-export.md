# ADR-0007: Nightly SFTP export of the delivery log

- Status: Accepted
- Date: 2023-02-15
- Governs: `src/export/sftp_export.py`

## Context
Three partners reconcile against a daily file rather than our webhooks.

## Decision
At 02:00 UTC, export the previous day's `delivery_attempts` rows per partner as CSV and push
them to each partner's SFTP server using `src/export/sftp_export.py`.
