From: Ines Marwood (Head of Platform, Kettleby Home)
Date: 3 November 2026
Subject: Catalogue search is moving to Postgres

Decided at Monday's platform review, and I'm not reopening it:

We move **product catalogue search** off the self-hosted search cluster and onto
Postgres full-text search, in the catalogue database we already run.

Why:
- The search cluster is our single most expensive piece of infrastructure.
- It caused four of last quarter's eleven out-of-hours pages.
- Only two people on the team know how to operate it, and one of them leaves in January.

**Help-centre article search stays on the search cluster for now.** It belongs to the
customer-care tools team and they are not ready to move. We'll revisit next year.

Risks I can see:
- Building the full-text index at cutover will take a while on the full catalogue.
- Result ranking will feel different to shoppers for a while.

Please write this up as an ADR in our usual format so it's on record before the work
starts. Target cutover is the week of 18 January 2027.

Ines
