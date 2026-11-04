# ADR-0003: Tenant isolation by row-level security

- Status: Accepted
- Date: 2024-09-19
- Deciders: Platform team, Security

## Context

All tenants share one database. A missed `WHERE tenant_id = ?` in application code leaked one tenant's customer list to another in a staging test (no production impact).

## Decision

Every tenant-owned table has a PostgreSQL row-level security policy on `tenant_id`. Each connection sets `app.tenant_id` at the start of a request or job, and queries run as the `app_tenant` role, which cannot bypass RLS. Background jobs must set the tenant from the job payload, never from a default.

## Consequences

- Code that runs outside a request (jobs, scripts) is responsible for setting the tenant before any query.
- Cross-tenant work (admin tooling) uses a separate audited role.
- Files produced from tenant data must be stored under a tenant-scoped prefix.

## Governs

- `services/billing-api/db/policies/`
- `services/jobs-worker/tenant_context.py`
- `infra/object-storage/`
