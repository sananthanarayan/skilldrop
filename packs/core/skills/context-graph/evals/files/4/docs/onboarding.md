# Welcome to Ledgerline

Ledgerline generates and sends customer invoices.

## Architecture in one page

- Postgres holds everything (ADR-0002).
- The nightly invoice run is scheduled by `src/ledgerline/scheduler/runner.py`. Only one
  worker may run it at a time, so it takes a Redis lock first (see ADR-0004).
- Money is integer cents (ADR-0009).

Last reviewed: 2023-09-14
