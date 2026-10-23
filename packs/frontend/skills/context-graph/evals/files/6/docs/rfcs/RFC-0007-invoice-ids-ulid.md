# RFC-0007: Switch invoice identifiers to ULIDs

- Status: Accepted
- Date: 2024-03-01
- Author: R. Achebe
- Supersedes: RFC-0003
- Governs: `services/invoicing/ids/`

## Proposal
Sequential IDs leaked customer invoice volumes and forced a single writer. Invoice IDs become ULIDs,
generated in-process, formatted `INV-<ulid>`. Existing `INV-000123` IDs stay valid.
