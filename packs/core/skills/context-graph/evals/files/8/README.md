# harbor-ledger

Double-entry ledger service for the Harbor payments platform.

- `services/ledger/` — the ledger service (Python)
- `api/` — service interface definitions
- `config/` — runtime configuration
- `docs/adr/` — architecture decision records
- `docs/rfcs/` — proposals under discussion

`services/ledger/api/gen/` is generated from `api/ledger.proto` at build time and is not checked in.
