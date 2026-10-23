# Worked example: Quayside Ledger article page

## Input

The user says: *"Our article pages feel janky and Search Console is unhappy. Here's a Lighthouse
run of the Harbour Bridge story. Our RUM dashboard says, for mobile over the last 28 days, LCP p75
3.4 s, INP p75 160 ms, CLS p75 0.31. What do we fix first?"* and supplies
[`quayside-article-lhr.json`](quayside-article-lhr.json), a hand-built Lighthouse 12 result
(default mobile, simulated throttling). All names and hosts are fictional.

The agent passes the RUM numbers to the script with the report:

```bash
python3 scripts/lh_summary.py examples/quayside-article-lhr.json \
  --lcp-p75 3400 --inp-p75 160 --cls-p75 0.31 --field-source "RUM, last 28 days, mobile"
```

## Script output (real; run header and main-thread section cut)

```markdown
## Field data (real users, p75): decides whether there is a problem
RUM, last 28 days, mobile

| Metric | p75 | Rating | Share good |
|---|---|---|---|
| LCP | 3.40 s | needs-improvement | - |
| INP | 160 ms | good | - |
| CLS | 0.31 | poor | - |

Core Web Vitals (field): FAILED: LCP needs-improvement, CLS poor

## Lab metrics (this run): explains why

Performance score: 78 (a lab weighting, not a Core Web Vitals result)

| Metric | Value | Lab rating | Threshold |
|---|---|---|---|
| FCP | 2.05 s | needs-improvement | good <= 1800ms, poor > 3000ms |
| LCP | 3.12 s | needs-improvement | good <= 2500ms, poor > 4000ms |
| TBT | 140 ms | good | good <= 200ms, poor > 600ms |
| CLS | 0.22 | needs-improvement | good <= 0.1, poor > 0.25 |
| Server response (lab TTFB) | 1.42 s | - | - |

## LCP element
Selector: article > figure.article-lead > img.article-lead__image
Flags: fetchpriority=high present

| Phase | Time | Share |
|---|---|---|
| TTFB | 1.65 s | 53% |
| Resource load delay | 180 ms | 6% |
| Resource load duration | 820 ms | 26% |
| Element render delay | 470 ms | 15% |
Dominant phase: TTFB

## Layout shift culprits (load window only; shifts after load are not in a lab run)
- body > div.ad-slot.ad-slot--top: 0.150, cause: Injected iframe (https://ads.adharbor.example/serve/frame.html)
- article > figure.article-lead > img.article-lead__image: 0.070, cause: Unsized image element

## Failing opportunities and diagnostics, ranked by the vital they move
| Audit | Est. load saving | Metric savings | Note |
|---|---|---|---|
| * server-response-time: Reduce initial server response time | 1.32 s | FCP 1.32 s, LCP 1.32 s |  |
| * unused-css-rules: Reduce unused CSS | 150 ms / 69 KiB | FCP 150 ms, LCP 150 ms |  |
| * layout-shifts: Avoid large layout shifts | - | CLS 0.22 |  |
| * unsized-images: Image elements do not have explicit width and height | - | none | acts on CLS directly |
```

## What the agent decides

- CLS is the vital furthest past its threshold (0.31 against 0.1, poor), so the shift fixes go
  first, even though the script's table lists the server fix first by milliseconds.
- The LCP image already has `fetchpriority="high"` and almost no load delay, so the preload
  advice a plain review gives would change nothing. TTFB is 53% of LCP: the server is the LCP fix.
- INP is good in the field, so TBT (140 ms) and the ad script's long task are not on the list.
- Field CLS (0.31) is above lab CLS (0.22): part of the shift happens after load, where this run
  can't see it.

## Reply

Readers do have a problem, and layout shift is the bigger one: on mobile, CLS at p75 is 0.31
(poor; good is 0.1) and LCP is 3.4 s (needs improvement; good is 2.5 s). Responsiveness is fine
(INP 160 ms). Most of the shift comes from the top ad slot, and most of the LCP time is spent
waiting for the server.

1. **Reserve space for the top ad.** `div.ad-slot--top` grows when the ad iframe arrives, which is
   0.15 of the 0.22 shift in this run. Give the slot a `min-height` equal to the tallest ad it serves
   on mobile. Moves CLS.
2. **Give the lead image dimensions.** `img.article-lead__image` (`bridge-1200.webp`) has no
   `width` or `height`, which is another 0.07 of the shift. Add both attributes, or an
   `aspect-ratio`, so the space is held before the image loads. Moves CLS.
3. **Cut the article's server response.** The HTML took 1.42 s to arrive, and time to first byte
   is 1.65 s of the 3.12 s lab LCP. Serve the article HTML from the CDN cache, or find where the
   backend spends that time. Lighthouse estimates up to 1.3 s off LCP in the lab. Moves LCP and FCP.
4. **Then trim the stylesheet.** `site.css` is 77% unused, about 150 ms of LCP in the lab. Small;
   do it after the three above.

What this run can't show: field CLS is higher than the run's 0.22, so some shifting happens after
load (later ads, scrolling) that a single page-load test doesn't record. RUM that reports which
element shifted would name it. The numbers come from one run on an emulated mid-range phone on
slow 4G; re-test with the median of three to five runs, then watch RUM p75 over the following weeks.

**To confirm:** the ad sizes the top slot serves on mobile, which set its `min-height`.
