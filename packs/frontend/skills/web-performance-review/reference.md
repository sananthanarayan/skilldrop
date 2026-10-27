# web-performance-review reference

## Thresholds

Core Web Vitals are judged at the 75th percentile of real page loads, per form factor.

| Metric | Good | Needs improvement | Poor | Field or lab |
|---|---|---|---|---|
| LCP | ≤ 2.5 s | 2.5–4 s | > 4 s | both |
| INP | ≤ 200 ms | 200–500 ms | > 500 ms | field only (or a Lighthouse timespan run) |
| CLS | ≤ 0.1 | 0.1–0.25 | > 0.25 | both; lab sees the load window only |
| FCP | ≤ 1.8 s | 1.8–3 s | > 3 s | both, supporting metric |
| TTFB | ≤ 0.8 s | 0.8–1.8 s | > 1.8 s | field; lab has `server-response-time` |
| TBT | ≤ 200 ms | 200–600 ms | > 600 ms | lab only, a proxy for INP |

A page passes Core Web Vitals when LCP, INP and CLS are all good at p75. With no INP data, CrUX
assesses on LCP and CLS.

The Performance score (Lighthouse 10 and later) weights lab metrics: TBT 30%, LCP 25%, CLS 25%,
FCP 10%, Speed Index 10%. It is a lab number. A page can score 90+ and fail every vital in the
field, or score 50 and pass.

## Fields the script reads

**Lighthouse result (LHR):** `lighthouseVersion`, `fetchTime`, `finalDisplayedUrl` (older:
`finalUrl`), `runWarnings`, `runtimeError`, `environment.benchmarkIndex`, `entities` (origins
grouped by company, `isFirstParty`), `configSettings.formFactor`, `.screenEmulation`,
`.throttlingMethod`, `.throttling` (`rttMs`, `throughputKbps`, `cpuSlowdownMultiplier`; the
`devtools` method uses `requestLatencyMs`, `downloadThroughputKbps`), `categories.performance.score`
(0–1), and `audits.<id>` with `score`, `scoreDisplayMode`, `numericValue`, `displayValue`,
`metricSavings` (Lighthouse 11 and later: `{LCP, FCP, TBT, CLS, INP}`) and `details`
(`type` is `opportunity`, `table`, `list` or `checklist`; rows in `details.items`; opportunities
add `overallSavingsMs` and `overallSavingsBytes`). An audit with score ≥ 0.9 passed.

**PageSpeed Insights v5:** `lighthouseResult` (the LHR), `loadingExperience` (this URL) and
`originLoadingExperience` (whole origin). Each has `metrics.<KEY>.percentile`, `.category`
(`FAST`, `AVERAGE`, `SLOW`) and `.distributions`. Keys: `LARGEST_CONTENTFUL_PAINT_MS`,
`INTERACTION_TO_NEXT_PAINT`, `CUMULATIVE_LAYOUT_SHIFT_SCORE` (**multiplied by 100**: 14 means
0.14), `FIRST_CONTENTFUL_PAINT_MS`, `EXPERIMENTAL_TIME_TO_FIRST_BYTE`. `origin_fallback: true`
means the URL had too little traffic and the numbers are the origin's. The PSI strategy (mobile
or desktop) sets which form factor the field data is.

**CrUX API record:** `record.key` (`url` or `origin`, `formFactor`), `record.metrics.<name>.percentiles.p75`
(CLS p75 is a string such as `"0.14"`), `histogram[0].density` (share good), `collectionPeriod`.

## Audits by the vital they act on

| Audit id | Acts on | Reads as |
|---|---|---|
| `largest-contentful-paint-element` | LCP | the element, and the phase table (`TTFB`, `Load Delay`, `Load Time`, `Render Delay`) |
| `lcp-lazy-loaded` | LCP | score 0 means the LCP image has `loading="lazy"` |
| `prioritize-lcp-image` | LCP | the LCP image is requested late; a preload or `fetchpriority` would start it sooner |
| `server-response-time`, `redirects`, `uses-rel-preconnect` | LCP, FCP | time before the first byte or first request |
| `render-blocking-resources` | FCP, LCP render delay | CSS or sync JS in the head |
| `uses-responsive-images`, `modern-image-formats`, `uses-optimized-images`, `offscreen-images` | LCP only when the LCP image is in the rows | otherwise bytes and load time |
| `unused-javascript`, `unused-css-rules`, `unminified-*`, `uses-text-compression` | whatever `metricSavings` says | often load time only |
| `layout-shifts` (older: `layout-shift-elements`), `unsized-images`, `font-display`, `non-composited-animations` | CLS | the element and the cause |
| `long-tasks`, `bootup-time`, `mainthread-work-breakdown`, `third-party-summary`, `third-party-facades` | TBT, a proxy for INP | scripts and entities by main-thread time |

Lighthouse 12 also emits `*-insight` audits (`lcp-breakdown-insight` or `lcp-phases-insight`,
`lcp-discovery-insight`, `cls-culprits-insight`, `third-parties-insight`,
`render-blocking-insight`); the script reads the LCP and third-party ones when the classic audit is
missing.

## LCP phases

| Phase | What it measures | When it dominates |
|---|---|---|
| TTFB | navigation start to the HTML's first byte | cache the HTML (CDN or edge), remove redirects, fix backend time |
| Resource load delay | first byte to the LCP resource's request | remove `loading="lazy"`, add `fetchpriority="high"`, put the `<img>` in the server HTML; a CSS background or JS-inserted image needs `<link rel="preload" as="image" fetchpriority="high">` |
| Resource load duration | the LCP resource's download | `srcset`/`sizes` matched to the viewport, AVIF or WebP, a CDN close to users |
| Element render delay | resource loaded to element painted | inline critical CSS, defer non-critical JS, avoid client-side rendering of the LCP element, break up long tasks before paint |

A text LCP element has zero load delay and duration. The healthy split puts most of the time in
TTFB and load duration, with load delay and render delay near zero.

## CLS causes Lighthouse reports

| Cause | Fix |
|---|---|
| Unsized image element | `width` and `height` attributes, or CSS `aspect-ratio` |
| Web font loaded | `font-display: optional` or `swap` with a `size-adjust`ed fallback; preload the font |
| Injected iframe, ad or banner | reserve the slot with `min-height`; overlay banners instead of pushing content |
| Media element | dimensions on `<video>` and embeds |
| Non-composited animation | animate `transform` and `opacity` only |

A navigation run records shifts during load. Shifts on scroll, after consent clicks or from late
ads count in field CLS and not in the lab, so field CLS above lab CLS points there; the web-vitals
library's attribution build reports the element per shift in RUM.

## Run settings

| Preset | RTT | Throughput | CPU | Screen |
|---|---|---|---|---|
| Default mobile (also PSI mobile) | 150 ms | 1.6 Mbps | 4x slowdown | 412 × 823 (Moto G Power) |
| `--preset=desktop` (also PSI desktop) | 40 ms | 10 Mbps | 1x | 1350 × 940 |

`throttlingMethod: simulate` (default) loads unthrottled and models the throttled timings, so
metrics are estimates; `devtools` applies throttling for real; `provided` applies none.
`benchmarkIndex` is the host CPU's score: a slow or busy machine inflates TBT and LCP. Runs
compare only with the same URL, preset, throttling, Lighthouse version and a similar host.
Lighthouse scores vary between runs of the same page; take the median of 3 to 5.

CrUX field data is a rolling 28 days, so a fix shows fully about four weeks after release. RUM
p75 for the same days shows it sooner.
