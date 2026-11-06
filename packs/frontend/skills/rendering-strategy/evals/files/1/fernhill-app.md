# Fernhill Outdoor — web shop rebuild

We sell hiking and climbing gear online. The current site is a client-rendered single-page app
and we lost a lot of Google traffic after launching it. We are rebuilding on **Next.js 15
(App Router)**, self-hosted on two Node containers behind a CDN that honours `Cache-Control`.

## The team's proposal

> Render every page with SSR (`export const dynamic = 'force-dynamic'` in the root layout).
> SSR is what fixes SEO, and it means every page always shows the right header and stock.

## Routes

| Route | What it shows | Pages | Page views / month |
|---|---|---:|---:|
| `/` home | hero, featured products, seasonal banners | 1 | 900,000 |
| `/c/[category]` product listing | product grid, filters as query params (`?size=`, `?colour=`, `?brand=`, `?sort=`) | 60 | 1,400,000 |
| `/p/[slug]` product detail | photos, description, price, reviews, **stock level** ("Only 3 left") | 4,000 | 2,600,000 |
| `/cart` | the user's basket | 1 | 380,000 |
| `/account` | orders, addresses, saved items | 1 | 150,000 |
| `/blog/[slug]` and `/blog` | trip reports and gear guides | 300 | 220,000 |

## What changes, and how fast

- **Product content and prices** live in our PIM. It sends a webhook on every product update.
  Prices change in a nightly batch plus a few flash sales a month. About 2,000 product updates
  a month in total.
- **Stock** comes from the inventory API. Twice a month we run a limited "drop": one product,
  a few hundred units, sold out in minutes. During a drop, the stock shown on the product page
  must be right to within 10 seconds or we get angry customers who saw "in stock" and then
  couldn't buy.
- The inventory API answers in about 180 ms normally; during drops it slows to 2–3 seconds and
  sometimes times out.
- **Blog** posts come from a headless CMS that sends a webhook on publish. About 12 posts a month.
- **Header:** every page shows "Hi, {first name}" and the cart count when the visitor is
  logged in. The design has it in the root layout, reading the session cookie.

## Ask

How should each route be rendered? We need to decide before the sprint starts.
