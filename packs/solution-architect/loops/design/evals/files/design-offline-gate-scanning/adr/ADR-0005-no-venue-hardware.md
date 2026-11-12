# ADR-0005: No Brindle-owned servers at venues

- **Status:** Accepted
- **Date:** 2025-06-30
- **Deciders:** Head of Engineering, Head of Venue Operations

## Context

We rent venues for one or two nights. Shipping, racking and securing servers at each venue was costed at 2 extra crew per show and made every venue's network team a dependency. Handhelds are lost or stolen a few times a tour.

## Decision

1. The only Brindle hardware at a venue is managed handhelds. No venue servers, appliances or laptops acting as servers.
2. Handhelds hold no long-lived secrets. Device credentials are short-lived (24 hours) and issued by device management; anything that can sign, mint or issue tickets stays in the cloud.

## Consequences

- Crew and kit per show stay small.
- A lost handheld can be revoked centrally and exposes nothing that outlives a day.
- Anything that must run at a venue must run on the handhelds themselves.
