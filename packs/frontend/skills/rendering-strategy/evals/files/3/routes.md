# Valley Courier — election night

Local news site on **Nuxt 3**, deployed on our own Node servers (Nitro) behind a CDN.

## Routes

| Route | What it shows | Pages | Traffic |
|---|---|---:|---|
| `/` | top stories, results ticker | 1 | 600,000 views / month |
| `/news/[slug]` | articles; metered paywall: anonymous readers get 5 free articles a month, with a "3 free articles left" bar | 12,000 | 4,000,000 views / month |
| `/topics/[topic]` | latest articles on one topic | 200 | 300,000 views / month |
| `/results/[race]` | live election results by race | 40 | expected 1,800,000 views between 21:00 and 03:00 on election night |
| `/account/**` | subscription, saved articles, newsletter settings | 3 | 40,000 views / month |

- The results feed updates about every 30 seconds on the night. Readers expect results no more
  than a minute old.
- The newsroom publishes about 150 articles a day and corrects some after publishing. The CMS
  sends a webhook on publish and on edit.
- The paywall meter is counted from a cookie.

## Draft config

```ts
export default defineNuxtConfig({
  routeRules: {
    '/': { swr: 300 },
    '/news/**': { ssr: true },     // per request, so the meter is right
    '/topics/**': { prerender: true },
    '/results/**': { ssr: true },  // must be live
    '/account/**': { swr: 60 },    // takes load off the servers
  },
})
```
