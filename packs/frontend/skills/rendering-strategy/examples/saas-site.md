# Worked example: SaaS marketing site, docs, status page and app (SvelteKit)

## Input

> We're moving Tallyhook (invoicing SaaS) to one SvelteKit app on Node behind a CDN. Routes:
> `/` and `/pricing` (marketing, edited a few times a month, the pricing table shows the
> visitor's currency from their country); `/docs/**` (about 500 pages, markdown in the repo,
> deployed on merge); `/changelog` (one entry a week); `/status` (must show an incident within
> 60 seconds, and has to work when the app is down); `/app/**` (the logged-in product).
> Traffic a month: marketing and changelog 300,000 views, docs 450,000, `/app` 900,000. We were
> going to set `ssr = true` everywhere and be done. How should each route render?

## Output

Don't render everything per request: only `/app` needs per-user pages, and even there the
choice is client- or server-rendered behind no shared cache. Everything public is prerendered
or cached, and the status page must not depend on the app at all.

| Route | Mode | Why | Invalidated by | When its source fails |
|---|---|---|---|---|
| `/`, `/pricing` | prerendered; currency picked by a CDN-geo cache key or a small client fragment | same for everyone in a country, indexed, shared | deploy (content is in the repo) `[assumption]` | page serves; currency falls back to USD `[assumption]` |
| `/docs/**` | prerendered (`export const prerender = true` on the docs layout), `csr = false` on pages with no widgets | same for everyone, indexed, changes only on merge | deploy on merge | served from the CDN |
| `/changelog` | prerendered | weekly change, indexed | deploy | served from the CDN |
| `/status` | static page on separate hosting, polling a status JSON with a 30-second TTL | must work when the app is down; 60-second freshness | the status JSON updates; the page never needs a rebuild | page loads; shows the last status with its time |
| `/app/**` | `ssr = false` (client-rendered SPA) or SSR with `private, no-store` | per user, never indexed | — | spinner, then an error state with retry |

**Traps found**

- `/status` inside the same SvelteKit app goes down with it. Host it apart from the app.
- Currency from geo makes `/pricing` vary per country: put the country in the CDN cache key
  (a few entries), not `Vary: Cookie` (one entry per visitor).
- `prerender = true` on the root layout would reach `/app` too; set it on the public layouts only.

**Cost.** SSR on every route: 1,650,000 renders a month. This plan: public pages render at
build only (500-odd pages per deploy); `/app` at most 900,000 if server-rendered, 0 if
client-rendered.

**To confirm**

- How often marketing pages are edited outside a deploy (if a CMS edits them, add an on-demand
  rebuild on its publish event).
- The fallback currency.
