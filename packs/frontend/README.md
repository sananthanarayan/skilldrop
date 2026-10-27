# Frontend

For frontend engineers and the people who review their pages: read a Lighthouse report for what actually slows the page, find what makes a JavaScript bundle heavy, and choose how each route is rendered from what it needs.

`/plugin install frontend@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Find out what actually makes a page slow for real users

Paste this into Claude Code:

```text
Here's report.json from Lighthouse for our product page. We score 92 in the lab, but Search Console says LCP is poor on mobile. What's making it slow for real users, and what should we fix first?
```

- **Before you start:** A Lighthouse JSON report for a slow page (`npx lighthouse <url> --output=json --output-path=report.json`), and its field data from PageSpeed Insights or Search Console if you have it
- **How to tell it worked:** web-performance-review leads with the field verdict (which vital fails at p75), names the LCP element and the phase that dominates it, and ranks fixes by how much each moves that vital, not by Lighthouse's estimated savings.
- **If nothing happens:** If the reply leads with the lab score or a generic checklist, ask for it by name ("use web-performance-review") and include the PageSpeed Insights JSON, which carries the field data.

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `bundle-size-review`
- `context-graph`
- `council-review`
- `doc-critique`
- `output-hygiene`
- `rendering-strategy`
- `web-performance-review`

More: https://sananthanarayan.github.io/skilldrop/packs/frontend/
