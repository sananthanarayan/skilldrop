# Observability platform: what we need (Pellingham Diagnostics)

Written by Anneke Vos (Head of Platform), 21 Sept 2026.

We're replacing the home-grown ELK box. Decision needed for the 16 Oct board prep.

## Facts
- 140 hosts today (112 prod, 28 non-prod). Expect about 160 by the end of 2027.
- Platform team: 3 engineers. One (Bashir) leaves at the end of November and the backfill is not approved.
- Log volume is about 90 GB/day. We need 30 days searchable.

## Must-haves (not negotiable)
1. All telemetry stored and processed in the EU. Logs contain patient sample IDs. Our DPO has confirmed this is a hard requirement from day one: no exceptions and no "coming soon".
2. Total cost at or under EUR 30,000 per year, all-in. That is what's in the 2027 budget.
3. SSO through our existing SAML identity provider.

## Nice-to-haves
- Fast log search. Devs complain the current one takes 20+ seconds.
- Alert routing into our pager.
- Not having to babysit it.
