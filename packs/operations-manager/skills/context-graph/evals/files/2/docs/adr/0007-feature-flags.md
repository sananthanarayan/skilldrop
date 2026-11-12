# 7. Feature flags in config, not a flag service

Date: 2025-06-09

## Context

We want to ship checkout changes dark and turn them on per region.

## Decision

Flags live in `services/checkout/flags.py` as a plain dictionary read at start-up. No external flag
service for now.

## Consequences

Turning a flag on needs a deploy.
