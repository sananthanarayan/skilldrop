# rendering-strategy reference

## Modes: what each costs and how each fails

| Mode | Renders | Fresh to | Personalised? | Indexed / previews | When the data source fails |
|---|---|---|---|---|---|
| Static at build (SSG) | once per build per page | last build | no (fragments only) | yes | page still served; data is as of the build |
| Revalidated (ISR, stale-while-revalidate, CDN `s-maxage` + `stale-while-revalidate`) | once per window per page that is visited, plus once per on-demand event | window, or the change event if on-demand | no (fragments only) | yes | last good copy keeps serving; regeneration retries |
| Server per request (SSR) | once per view | the request | yes | yes | TTFB waits on the slowest call; without a timeout the page errors or hangs |
| SSR streaming | once per view; shell first | the request | yes | yes, for content in the shell | shell arrives; the slow part shows its placeholder or fallback |
| Edge render | once per view, near the user | the request | yes, from cookie or geo | yes | as SSR, and every data call still travels to the origin region |
| Client-rendered (CSR, SPA) | none on the server; one data call or more per view | the request | yes | no: crawlers and preview bots get an empty shell | spinner, then an error state; nothing without JavaScript |
| Islands / server components | per the page's mode; only interactive parts ship JavaScript | per the page's mode | the island can be | yes | per the page's mode; an island can fail alone |

Two rules the table implies:

- **Revalidation reduces renders only when a page gets more views than windows.** A long tail
  of pages each viewed a few times a month renders about once per view under a 5-minute
  window. On-demand revalidation on the real change event is the saving.
- **Edge rendering is not faster when the data is in one region.** The HTML starts near the
  user and then waits on a round trip to the origin database. It pays off for decisions made
  from the request alone (geo, cookie, A/B bucket) or data replicated to the edge.

## Splitting a page

| The page has… | Render the page | Render the part |
|---|---|---|
| A greeting, avatar or cart count | cached (static or revalidated) | client fetch to a `private, no-store` endpoint after load, or an edge-rendered fragment |
| A stock, price or seat count that must be fresh within seconds | cached | client fetch to an endpoint with a CDN TTL at or under the tolerance (which also collapses a spike to one origin call per TTL); the authoritative check at checkout |
| Recommendations per user | cached | client island, lazy, below the fold |
| A/B variant or locale | cached per variant (variant in the cache key, not a cookie `Vary`) | — |
| Whole page differs per user (dashboard, orders, settings) | per request or client-rendered, never shared-cached | — |

## Cache headers

- Shared, revalidated HTML: `Cache-Control: public, s-maxage=<window>, stale-while-revalidate=<grace>`.
- Personalised HTML or JSON: `Cache-Control: private, no-store`. Never rely on `Vary: Cookie` to
  separate users at a CDN: many CDNs ignore it or it turns the hit rate to zero.
- A response with `Set-Cookie` is never stored in a shared cache. Check the CDN's default.
- Query strings: list the parameters that change the content (`?category=`, `?page=`) and strip
  or ignore tracking ones (`utm_*`, `gclid`) from the cache key. Faceted combinations that
  explode the key space are rendered client-side from a cached listing, or get `noindex` and a
  canonical URL.

## Invalidation events

Write each as event → pages:

- Content publish or edit in a CMS → the page, its index and listing pages, the sitemap.
- Product, price or stock-threshold change in a catalogue system → the product page, its
  category pages, any page featuring it (home carousel).
- Deploy → every static page rebuilt; say whether a deploy is the only way a page changes.
- Time → only for data with no event (exchange rates polled, aggregated counts).

## Framework settings

Use only the section for the framework the user named. Behaviour that changed between major
versions is marked; confirm the version in `package.json` before stating it.

### Next.js

- **App Router.** Route segment config per route: `export const revalidate = 600` (time-based),
  `export const dynamic = 'force-static'` or `'force-dynamic'`; `generateStaticParams` to
  prerender dynamic segments. On-demand: `revalidatePath('/p/slug')` or `revalidateTag('product:123')`
  from a route handler the webhook calls; tag the fetch with `next: { tags: [...] }`.
- **The trap:** calling `cookies()` or `headers()` in a layout makes every route under it
  dynamic. A greeting in the root layout turns the whole site into per-request SSR. Move the
  personal part into a client component that fetches after load, or behind `<Suspense>`.
  Reading `searchParams` in a page does the same to that page: filters and sorting as query
  strings make a listing dynamic. Filter client-side over the cached listing, or make the
  indexed combinations path segments with `generateStaticParams`.
- **Version-dependent:** the default caching of `fetch` changed between major versions (cached by
  default earlier, not cached by default from 15). Partial prerendering and the `"use cache"`
  directive are experimental in some versions. State the version before relying on any of these.
- **Pages Router.** `getStaticProps` with `revalidate`, `getStaticPaths` with `fallback: 'blocking'`,
  `getServerSideProps` for per request, `res.revalidate()` for on-demand.

### Nuxt

- `routeRules` in `nuxt.config`: `{ prerender: true }` (static at build), `{ swr: 600 }` (cached
  response with background revalidation), `{ isr: 600 }` (the same on hosts with ISR support,
  such as Vercel or Netlify), `{ ssr: false }` (client-rendered), `{ headers: { 'cache-control': ... } }`.
- **The trap:** `swr` and `isr` cache the rendered response keyed by path, shared across users.
  On a personalised path they serve one user's page to everyone. Personalised routes get
  `{ ssr: false }` or no cache rule plus `private, no-store`.
- `prerender: true` on a page that changes between deploys freezes it until the next build.

### Remix / React Router (framework mode)

- Rendering is per request by default; caching is the `Cache-Control` the route's `headers`
  export returns (`public, s-maxage=…, stale-while-revalidate=…` for shared, `private, no-store`
  for personal). The CDN does the revalidation.
- Slow data: return the promise from the loader without awaiting it and render it with
  `<Await>` inside `<Suspense>`, so the shell streams first.
- **Version-dependent:** React Router 7 adds `prerender` and `ssr: false` in
  `react-router.config.ts` for static and SPA modes; Remix 2 has neither.

### SvelteKit

- Per route in `+page.js` / `+page.server.js` or a layout: `export const prerender = true`,
  `export const ssr = false` (client-rendered), `export const csr = false` (no JavaScript at all
  for a read-only page). `setHeaders({ 'cache-control': ... })` in `load` for CDN caching.
- ISR is adapter-specific (for example `export const config = { isr: { expiration: 600 } }` on the
  Vercel adapter); on other adapters use CDN headers.
- **The trap:** `prerender = true` on a layout applies to every child route, including ones that
  need the request (cookies, `url.searchParams`); the build errors on them or the personal part
  is rendered once at build. Set it per route, or override with `prerender = false` below.

### Astro

- Static by default. Per page: `export const prerender = false` to render on request (needs an
  adapter); site-wide `output: 'server'` flips the default.
- Islands: `client:load`, `client:idle`, `client:visible` hydrate one component; everything else
  ships no JavaScript. Server islands (`server:defer`) render a personal fragment per request
  inside a cached static page — the direct fit for a greeting on a static page.
- **Version-dependent:** server islands need a version that supports `server:defer`.
