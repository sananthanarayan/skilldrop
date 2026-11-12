# ADR-0011: Self-hosted search cluster for catalogue and help-centre search

## Status
Accepted

## Context
Shoppers searching the catalogue with typos ("cusion", "tealight holdr") got no results;
18% of catalogue searches returned nothing. The customer-care team also needed search over
help-centre articles.

## Decision
1. Catalogue search runs on a self-hosted search cluster, with typo-tolerant (fuzzy)
   matching and synonyms ("sofa" finds "couch").
2. Help-centre article search runs on the same cluster, in a separate index owned by the
   customer-care tools team.
3. The cluster is fed from the catalogue database by a change-capture job every minute.

## Consequences and risks
Zero-result searches fell from 18% to 4%. The cluster is a second system to operate and
page on. Owner: platform team (cluster), customer-care tools team (help-centre index).

## Alternatives considered
Postgres full-text search; rejected at the time because it does no typo-tolerant matching
out of the box.
