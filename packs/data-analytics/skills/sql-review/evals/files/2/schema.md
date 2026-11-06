# Schema (fundraising database, PostgreSQL 16)

## donations

| column | type | notes |
|---|---|---|
| donation_id | bigint | primary key |
| donor_id | bigint | |
| donated_at | timestamptz | stored in UTC |
| amount_pence | bigint | refunds are recorded as separate rows with a negative amount |
| gift_aid_status | text | 'claimed', 'rejected', or NULL when the donor has never made a Gift Aid declaration (most donors) |

## donor_addresses

| column | type | notes |
|---|---|---|
| address_id | bigint | primary key |
| donor_id | bigint | a donor can have several addresses (home, work, previous) |
| region | text | |
| is_primary | boolean | exactly one primary address per donor |
