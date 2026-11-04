# Tallyhall — merged to main for "saved searches v2" (release train 2026.45)

All merged between 26 Oct and 3 Nov 2026. Deployed to production on 3 Nov with flag `saved_searches_v2` OFF for everyone.

| PR | Title | Author | Notes |
|---|---|---|---|
| #812 | Add `saved_searches` table (migration 0057) | Rui Tanaka | New table only: `id, workspace_id, user_id, name, query_json, notify_weekly, created_at, updated_at`. No changes to existing tables. Ran in production on 3 Nov, 0.4s. |
| #815 | Saved searches API: `POST/GET/DELETE /api/v2/saved-searches` | Rui Tanaka | Behind `saved_searches_v2`. Max 50 saved searches per user (returns 422 above that). |
| #819 | Saved searches in the sidebar | Elif Demir | Behind `saved_searches_v2`. Save the current search from the search bar; rename; delete. |
| #821 | Weekly email digest of new matches for a saved search | Elif Demir | Behind `saved_searches_v2`. Opt-in per saved search (`notify_weekly`). New job `saved-search-digest` runs Mondays 06:00 UTC. |
| #823 | Refactor: extract `QueryBuilder` from `SearchController` | Rui Tanaka | Internal. No behaviour change. |
| #824 | CI: bump Node to 22 in build image | Platform bot | Internal. |
| #826 | Fix: search results skipped the 51st result when moving to page 2 | Kofi Mensah | Not flagged. Live since the 3 Nov deploy. |
