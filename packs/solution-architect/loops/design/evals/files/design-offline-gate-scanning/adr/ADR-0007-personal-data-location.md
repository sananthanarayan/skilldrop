# ADR-0007: Where fans' personal data may be stored

- **Status:** Accepted
- **Date:** 2026-01-19
- **Deciders:** Head of Engineering, Data Protection Officer

## Context

Fans' names, emails and phone numbers are personal data. A handheld left in a venue after a show was found with cached API responses on it in late 2025.

## Decision

1. Fans' personal data is stored only in our eu-west cloud services.
2. Handhelds must not store fans' personal data, not even temporarily. They may display it when the API returns it, and must not write it to disk.

## Consequences

- A lost handheld does not leak fans' details.
- Features that show personal data at the gate depend on the handheld being online.
