# Architecture sync, Tuesday 10 November 2026

**Present:** Rosalind Achebe-Marr (Head of Engineering, decider), Kofi Brandt-Lyle (platform), Nell Szabo-Price (SRE), Arun Tiwell (product)

## Item 1: Tenant databases

**Background (Kofi).** We run one Postgres database per customer (ADR-0002). We now have 14 tenants across two clusters. Each new tenant means a new database, new backup policy, new monitoring, and every schema migration runs 14 times. Last quarter two migrations half-applied and needed hand fixing. Hosting for the two clusters is about £9,400 a month; most tenant databases sit under 5% busy.

**Proposal.** Move every tenant into one shared database on `pg-main`, with a `tenant_id` column on every tenant-owned table and Postgres row-level security (RLS) as the tenant boundary. Retire `pg-eu1` afterwards.

**Discussion.**
- Nell: per-tenant restore gets harder; we'd restore to a side database and copy the tenant's rows back. Needs a runbook.
- Arun: no customer-visible change expected.
- Kofi: estimated hosting after consolidation about £3,900 a month, one migration run instead of 14.

**Decision (Rosalind).** We consolidate. One shared database on `pg-main`, `tenant_id` + RLS, `pg-eu1` retired once empty. Migration to be planned by platform; Kofi to bring a plan to the sync in two weeks. This is decided; I don't want to reopen it. Please get the ADR written up so it's on record before planning starts.

**Actions.**
- Kofi: migration plan, next sync.
- Nell: per-tenant restore runbook.
- (unassigned) ADR for the decision.
