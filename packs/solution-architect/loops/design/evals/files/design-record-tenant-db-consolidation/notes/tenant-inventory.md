# Tenant inventory

Maintained by the platform team. Last checked 2 November 2026.

| Tenant | Database | Cluster | Region | Notes |
|--------|----------|---------|--------|-------|
| Ashcombe & Pryor | t_ashcombe | pg-main | uk-south | |
| Bellweather Accounts | t_bellweather | pg-main | uk-south | |
| Corran Tax | t_corran | pg-main | uk-south | |
| Dunmore Practice | t_dunmore | pg-main | uk-south | |
| Elstow Partners | t_elstow | pg-main | uk-south | |
| Fenrow Lowe | t_fenrow | pg-main | uk-south | largest tenant, ~40% of rows |
| Greythorn Ledger | t_greythorn | pg-main | uk-south | |
| Hartfield Books | t_hartfield | pg-main | uk-south | |
| Ivel Accountancy | t_ivel | pg-main | uk-south | |
| Jessop Marr | t_jessop | pg-main | uk-south | |
| Kittering & Co | t_kittering | pg-main | uk-south | |
| Lanyard Finance | t_lanyard | pg-main | uk-south | |
| Mosel Steuerberatung | t_mosel | pg-eu1 | eu-central | see customer-commitments.md |
| Norderhof Treuhand | t_norderhof | pg-eu1 | eu-central | see customer-commitments.md |

## Clusters

- `pg-main`: uk-south. Primary plus one replica.
- `pg-eu1`: eu-central. Primary plus one replica. Only the two tenants above.
