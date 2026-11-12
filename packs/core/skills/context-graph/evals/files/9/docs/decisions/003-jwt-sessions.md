# RFC 003 — Stateless JWT sessions

| Field   | Value      |
|---------|------------|
| State   | Proposed   |
| Author  | r.achebe   |
| Created | 2026-09-02 |
| Replaces | 001       |

## Motivation

Mobile clients want a bearer token rather than a cookie, and we would like login to keep
working during a Redis restart.

## Proposal

Issue a signed access token (15 minutes) and a refresh token (7 days). The app verifies the
signature locally; no session lookup per request.

## Open questions

1. **Revocation.** Logout and "sign out everywhere" need to invalidate tokens before they
   expire. Current thinking: keep a denylist of revoked token ids in Redis with a TTL equal to
   the token's remaining lifetime.
2. Key rotation schedule — needs a decision before this is accepted.

## Status of discussion

Not yet reviewed by the platform team.
