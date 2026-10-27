---
name: rendering-strategy
description: Decide route by route how each page of a web app is rendered — static at build (SSG), static with revalidation (ISR, stale-while-revalidate), server-rendered per request (SSR, streaming), client-rendered (CSR, SPA), at the edge, or a mix with islands and server components — from how fresh each route's data must be, whether it is personalised, whether it must be indexed or shared, what it costs per request at the stated traffic and how much JavaScript it needs, with the cache keys, invalidation events and failure modes of each choice. Use when the user asks "should this be SSR or static", "SSR vs SSG vs ISR", "how should each page be rendered", "do we need SSR for SEO", "which pages can we cache", or is choosing rendering modes in Next.js, Nuxt, Remix, React Router, SvelteKit or Astro.
---

# rendering-strategy

Picks a rendering mode for every route of a web app and records why: what the route needs, the
mode that meets it at the lowest cost, what invalidates it, and what the user sees when its data
source fails. It decides rendering, not the whole system: the system design is `design-doc`,
latency and availability targets are `nfr-spec`, and recording the chosen strategy as a
decision record is `adr-generator`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** Decide per route, never per app. A page that is the same for everyone and can be minutes stale is cached, and the personalised or seconds-fresh part of a page is rendered on its own, never used as the reason to render the whole page per request.

1. **List the routes and what is known about each.** One row per route or route group: how
   fresh its data must be, whether it differs per user, whether it must be indexed or shared,
   its traffic, and what on it is interactive. Take these from the input only. Traffic,
   freshness and framework version are never invented: ask at most two questions (the
   freshness of the most volatile data, then traffic), or tag the gap `[assumption]`.

2. **Ask the five questions for each route, in this order.** The first answer that settles the
   mode wins; later questions refine it.
   1. **How fresh must the data be?** "Minutes stale is fine" → cacheable. "Within seconds" →
      only that field is fresh, the page still caches (step 3).
   2. **Is it the same for everyone?** Same → static or revalidated. Personalised in one corner →
      cached page plus a personal fragment. Personalised throughout → per request, never cached.
   3. **Must it be indexed or shared with a preview?** Then the content and the preview meta
      tags are in the HTML at first byte: static, revalidated or server-rendered, never
      client-only.
   4. **What does it cost per request at the stated traffic?** Count renders (step 5).
   5. **How much JavaScript does it need?** Read-only content ships none or islands; a dense
      app screen can be client-rendered.

   ✅ *"Blog post: changes on publish, same for everyone, must be indexed → static, rebuilt on
   the CMS publish event."* — ❌ *"Blog post: SSR, for SEO."*

3. **Split the page, not the mode.** A personalised header, a cart count or a stock figure is a
   fragment: fetched on the client after a cached page loads, rendered at the edge, or streamed
   into a static shell (islands, server islands, partial prerendering).
   ✅ *"Home: revalidated every 10 min; the 'Hi, Sam' greeting and cart badge load client-side
   from `/api/me`."* — ❌ *"Home must be SSR because the header shows the user's name."*
   A value that must be fresh within seconds is never left to time-based revalidation: a
   stale-while-revalidate cache serves the old page to the first visitor after the window
   ends. ✅ *"Product page cached; stock fetched from a 5-second-TTL endpoint; checkout
   re-checks stock."* — ❌ *"Product page ISR with revalidate: 5 so stock is fresh."* A
   CDN TTL on that endpoint also turns a traffic spike into one origin call per TTL per item.

4. **Treat SEO as an HTML question, not an SSR question.** Crawlers and link-preview bots need
   the content and `og:` tags in the first response. A static page has them; so does a
   revalidated one. CSR is wrong for any page that must be indexed or shared, and right for
   logged-in screens nobody searches for.
   ✅ *"Marketing pages prerendered; the logged-in app stays a client-rendered SPA."* —
   ❌ *"Move the whole app to SSR so Google can see it."*

5. **Put a number on cost.** When the input gives traffic, write the routes as a CSV (columns
   in the script header: `route, mode, views_month, pages, revalidate_s, changes_month,
   builds_month`) and count origin renders under the proposed mode against per-request SSR:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/render_load.py" routes.csv
   # Other IDEs (from the skill folder)
   python3 scripts/render_load.py routes.csv
   ```

   The count also shows when time-based revalidation saves nothing: a long-tail route whose
   pages each get fewer views than revalidation windows renders nearly once per view, so
   on-demand revalidation on the change event is the saving. If no script can run, do the
   same arithmetic by hand and show it. Without traffic, state the comparison as "one render
   per view vs one per change" and list traffic under To confirm.

6. **Name the cache key and the invalidation event for every cached route.** What event
   invalidates which pages, and what must never reach a shared cache.
   ✅ *"Product updated in the PIM → webhook revalidates `/p/[slug]` and its category pages.
   Cart and account: `Cache-Control: private, no-store`."* — ❌ *"Cache with a 60-second
   TTL."* Filter and sort query strings multiply cache entries: name the parameters that are
   part of the key and drop the rest.

7. **Name the failure mode of each row.** What the user sees when the data source is slow or
   down. SSR ties time to first byte to the slowest call: say the timeout and the fallback, or
   stream the slow part behind a placeholder. Revalidated pages serve the last good copy on
   failure. CSR shows a spinner, and nothing without JavaScript. ✅ *"Stock call times out at
   800 ms → page shows 'Check availability' and the add-to-cart button still works."*

8. **Use framework terms only for the framework the user named.** Then give the exact setting
   per route from [`reference.md`](reference.md), flag anything that depends on the version in
   `package.json`, and catch the framework trap (a cookie read in a shared layout that makes
   every route dynamic; a server cache rule on a personalised path). No framework named →
   neutral terms only.

9. **Write it up, lean.** First line: the answer, including whether the team's proposal
   stands. Then the route table: route, mode, why (freshness / personalised / indexed),
   invalidation, failure mode. Then the traps found, each in one or two lines, the cost
   numbers if traffic was given, and To confirm. No section for a question nobody asked.

**Non-interactive runs** (subagent, CI, headless): missing traffic, freshness tolerances or
framework version become `[assumption]` rows listed at the top under To confirm. A request
that names no routes, pages or app at all emits `BLOCKED: need the app's routes and what each
page shows`, because a route table of invented pages decides nothing.

## Useful references in this skill

- [`reference.md`](reference.md) — the mode-by-mode cost and failure table, cache headers that are safe for personalised pages, and per-framework settings for Next.js, Nuxt, Remix / React Router, SvelteKit and Astro
- [`scripts/render_load.py`](scripts/render_load.py) — counts origin renders per month per route against per-request SSR (stdlib only)
- [`examples/saas-site.md`](examples/saas-site.md) — worked example: marketing site, docs, status page and app in SvelteKit

## Quality bar

- **One row per route or route group,** each with a mode and the deciding reason. One mode for the whole app fails.
- **Every cached route names its invalidation event** and the pages it touches; time alone is not an invalidation plan for data that changes on an event.
- **Every personalised response is named as never shared-cached** (`private, no-store`, or kept off the cached page as a fragment).
- **Seconds-fresh data is a fragment with its own short-lived source,** not the page's revalidation window.
- **Every row has a failure mode:** what the user sees when its data source is slow or down.
- **Cost is a computed number when traffic is given,** from the input's figures only.
- **Framework settings appear only for the named framework,** and version-dependent behaviour is flagged.
- **Nothing invented:** traffic, freshness and versions come from the input or carry `[assumption]`.

## When to use this skill

- ✅ "Should these pages be SSR, static or ISR?" for an app with several kinds of page
- ✅ A team proposing SSR (or an SPA) everywhere and wanting it checked
- ✅ "Our pages don't show up in Google / link previews are blank" on a client-rendered site
- ✅ Setting route rules, revalidation and cache headers in a named framework

## When NOT to use this skill

- ❌ Designing the whole system (services, data stores, rollout) — `design-doc`
- ❌ Writing the chosen strategy up as a numbered decision record — `adr-generator`
- ❌ Setting latency or availability targets for the app — `nfr-spec`
- ❌ Diagnosing why a page is slow from a Lighthouse report — that is a page-speed review, not a rendering decision

## Anti-patterns to avoid

- ❌ **SSR everywhere "for SEO."** It pays a render per view for pages that are the same for everyone and could be served from a CDN.
- ❌ **A personalised header forcing the site dynamic.** A name and a cart count are a fragment, not a rendering mode.
- ❌ **Short revalidation as a freshness guarantee.** Stale-while-revalidate serves the stale copy first; a 5-second window across thousands of pages is also thousands of regenerations nobody needed.
- ❌ **CSR for a page that must be indexed or shared.** Preview bots don't run JavaScript; the card is blank.
- ❌ **Caching a logged-in page at the CDN.** One user's account page served to the next visitor is a data leak, not a performance win.
- ❌ **SSR with no timeout.** The page is as slow as the slowest API it calls, and fails with it.
- ❌ **Framework advice for a framework nobody named,** or version-specific settings stated without the version.
