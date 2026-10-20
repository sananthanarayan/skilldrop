---
name: web-performance-review
description: Read a Lighthouse report or PageSpeed Insights result, with field data when there is any (CrUX, PSI loadingExperience or RUM p75), and say what makes the page slow for real users and what to fix first, ranked by how much each fix moves LCP, INP and CLS at the 75th percentile. Names the LCP element and which LCP phase dominates, the elements that shift and why, the long tasks and third parties by main-thread time, and treats estimated savings as lab estimates that overlap. Use when the user shares a Lighthouse JSON or PSI result and asks "why is this page slow", "what should we fix first", "we score 92 but Search Console says LCP is poor", "did our change fix INP", "review this Lighthouse report", or "how do we pass Core Web Vitals".
---

# web-performance-review

Reads a Lighthouse run the way a performance engineer does: real-user p75 numbers decide whether
the page has a problem, and the one lab run explains why. The output names the element, the URL
and the change, in the order that moves the failing vital most. Accessibility findings in the
same report go to `accessibility-audit`. What is inside a heavy JavaScript bundle is a
bundle analysis from the bundler's stats file, not this report. Choosing SSR, static or client rendering for a route is
`rendering-strategy`. Setting up RUM or alerting on the vitals is `observability-plan`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** Field p75 decides whether there is a problem; the lab run explains why. Never call a page good or bad from the Performance score, and say which data each verdict rests on.

1. **Get the report and any field data.** Accept the Lighthouse JSON, a PageSpeed Insights API response (it embeds the Lighthouse result and the CrUX field data), a CrUX API record, or RUM p75 numbers typed in the message. Ask once, in one sentence, for field data when there is none; never hold the review back for it. When the user can run Lighthouse, ask for three to five runs, not one:
   ```bash
   for i in 1 2 3 4 5; do npx lighthouse "$URL" --only-categories=performance --output=json --output-path="run-$i.json" --quiet --chrome-flags="--headless"; done
   ```
   An installed CLI is the same command without `npx`: `lighthouse "$URL" --output=json --output-path=report.json`.

2. **Run the summary script; read numbers from it, not by eye.** It prints the run settings, lab metrics against thresholds, field p75 with ratings and the Core Web Vitals outcome, the LCP element and phases, layout-shift culprits, failing audits ranked by the vital they move (with overlaps marked), long tasks and third parties, and render-blocking resources. It exits 2 on a file that is not a Lighthouse, PSI or CrUX result.
   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/lh_summary.py" psi.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/lh_summary.py" report.json --lcp-p75 3100 --inp-p75 420 --cls-p75 0.04
   python3 "${CLAUDE_SKILL_DIR}/scripts/lh_summary.py" before.json after.json
   # Other IDEs (from the skill folder)
   python3 scripts/lh_summary.py psi.json --json
   ```
   Pass RUM numbers with `--lcp-p75 / --inp-p75 / --cls-p75` and a CrUX file with `--field`. Two reports print a comparability check and the deltas. When only a pasted excerpt is available, apply the same steps by hand and say which sections were not in the excerpt.

3. **Give the verdict from field data, per vital, with the threshold and the source.** Good at p75 is LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1; poor is LCP > 4 s, INP > 500 ms, CLS > 0.25. Say whether the numbers are for this URL or the whole origin (PSI's `origin_fallback`), and the form factor.
   - ✅ *"Real mobile users wait 4.3 s for the main image at p75 (poor; good is 2.5 s). The 92 is one simulated lab load, and its 2.4 s LCP is not what users get."*
   - ❌ *"The page scores 92, so performance is good; LCP could be improved slightly."*
   - With no field data: ✅ *"Whether the page passes Core Web Vitals can't be told from a lab run. This run shows LCP at 3.1 s in the lab, and here is why."* PSI reports CLS p75 multiplied by 100: `14` is 0.14.

4. **Name the LCP element and fix the phase that dominates.** Quote the element's selector or snippet and split LCP into TTFB, resource load delay, resource load duration and element render delay. The biggest phase picks the fix:
   - **Load delay** dominates: the browser found the resource late. `loading="lazy"` on the LCP image, no `fetchpriority="high"`, or an image set from JS or a CSS `background-image` (which needs an `<img>` in the HTML, or `<link rel="preload" as="image" fetchpriority="high">`). ✅ *"Remove `loading=\"lazy\"` from `img.collection-hero__image` and add `fetchpriority=\"high\"`; it is in the HTML already, so it needs no preload."* ❌ *"Optimize images."*
   - **TTFB** dominates: server time, redirects or no HTML caching.
   - Field TTFB needs improvement or worse while lab TTFB is small: say part of the field LCP is server and network time the lab run can't show. The lab measures one request from one place.
   - **Load duration** dominates: the file is too large for the viewport (a 2400 px image on a 412 px screen). Name the URL and the `srcset` widths.
   - **Render delay** dominates: render-blocking CSS or JS, client-side rendering, or long tasks before paint. A text LCP element has no resource, so all of its time is TTFB plus render delay.

5. **Name what shifts and why.** For each shifting element give its score and the cause the report gives: unsized image → `width`/`height` or `aspect-ratio`; web font → `font-display` plus a size-adjusted fallback; injected iframe or banner → reserve the slot with `min-height`. A lab run sees only shifts during load. When field CLS is worse than lab CLS, say the extra comes from shifts after load (scrolling, late banners, ads) that this report can't show, and say what would show them.

6. **Treat TBT as a lab proxy for INP, never as INP.** Name the long tasks by script and the third parties by entity with their main-thread and blocking time: ✅ *"ChatterBox's loader.js: one 170 ms task at 3.1 s; 412 ms of main-thread time in total."* When field INP is good, TBT is not a priority, whatever the score weights say. When field INP is poor, point at the scripts that run on interaction too, because a navigation run records no interactions.

7. **Rank fixes by the failing vital they move, and how much.** Fixes for the vital furthest past its field threshold come first, even when the script's table lists another first. Within a vital, use the audit's per-metric saving (`metricSavings`), not the headline "Est savings", which is lab load time. An audit with a big load saving and no LCP, TBT or CLS saving goes last or is left out: ✅ *"Converting the product-grid JPEGs saves 1.2 MB but does not move LCP; the LCP image is the hero."* Savings that touch the same resource overlap: never add them into a total. Give each fix as the change, on the named element or URL, and the vital it moves.

8. **Say how sure the numbers are.** One run is noisy: say so once, name the emulated device and throttling (Lighthouse's default mobile is a mid-range phone on slow 4G with 4x CPU slowdown), and note any run warnings. Before calling a change an improvement, ask for the median of 3 to 5 runs per side with the same settings, then field data. Runs with different device, throttling or Lighthouse version are not comparable, and the script lists every such difference. CrUX is a 28-day rolling window, so it trails a fix by weeks; RUM shows it sooner.

9. **Write the reply in this order.** First, two or three sentences: whether real users have a problem, on which vital, and the main cause. Then up to five numbered fixes, each with the change, where, the vital it moves and the evidence. Then one short paragraph on what this report can't tell. Add "To confirm" only for missing inputs. Leave out the metric tables unless the user asked for them, keep a chat question to a chat-length answer, and keep to any word limit the user sets.

**Non-interactive runs** (subagent, CI, headless): missing field data becomes `[assumption] no field data given; Core Web Vitals pass/fail not stated, lab findings only`, stated first. A missing report, a report with `runtimeError`, or a file the script rejects emits `BLOCKED: need the Lighthouse JSON (lighthouse <url> --output=json) or the PageSpeed Insights API response for the page`. Never review a report that failed to load the page.

## Useful references in this skill

- [`reference.md`](reference.md): thresholds, the Lighthouse and PSI fields read, LCP phases and their fixes, CLS causes, audit-to-vital map, throttling presets, field-data quirks
- [`scripts/lh_summary.py`](scripts/lh_summary.py): stdlib summariser for Lighthouse, PSI and CrUX JSON; `--json`, `-o`, two-report comparison; exits 2 on bad input
- [`examples/quayside-article.md`](examples/quayside-article.md): worked example, a news article with poor field CLS from an ad slot and a TTFB-heavy LCP

## Quality bar

- **The first lines say whether real users have a problem**, on which vital, from which data, with the p75 threshold.
- **No verdict from the Performance score.** The score is described as a lab weighting, not as Core Web Vitals.
- **The LCP element is named** by selector or snippet, with the phase breakdown when the report has it, and the fix matches the dominant phase.
- **Every CLS fix names the shifting element and its cause**; field CLS above lab CLS is called out as after-load shifts the run can't see.
- **TBT is never reported as INP.** Long tasks and third parties are named by script or entity with milliseconds.
- **Fixes are ranked by the failing vital's per-metric saving**, load-time-only savings are not ranked as vital fixes, and overlapping savings are not summed.
- **The single-run caveat and the emulated device and network appear once**, with medians of 3 to 5 runs or field data as the bar for "improved".
- **No invented numbers, elements or URLs.** Every figure and selector is in the input or computed from it.

## When to use this skill

- ✅ A Lighthouse JSON or PSI result is shared with "why is this slow" or "what do we fix first"
- ✅ The lab score and Search Console or CrUX disagree
- ✅ Checking whether a performance change worked, from before and after runs
- ✅ Planning Core Web Vitals work for a page from its report and RUM numbers

## When NOT to use this skill

- ❌ The accessibility findings in the same Lighthouse report: use `accessibility-audit`
- ❌ What is in a JavaScript bundle and why it is heavy (source maps, stats files): that needs the bundler's stats file, not a Lighthouse report
- ❌ Choosing SSR, static, ISR or client rendering for routes: use `rendering-strategy`
- ❌ Setting up RUM, web-vitals collection, dashboards or alerts: use `observability-plan`
- ❌ Lighthouse SEO and Best Practices scores; this skill reads the Performance category only

## Anti-patterns to avoid

- ❌ **"92, so it's fine."** The score weights one simulated load; it says nothing about users on slower phones and networks.
- ❌ **Calling TBT "INP".** A load run has no clicks or taps. INP comes from field data.
- ❌ **Leading with the biggest "Est savings".** It is page load time in the lab, often for images below the fold.
- ❌ **Adding savings up.** "Fix these four for 5.9 s" double-counts the same images and the same main thread.
- ❌ **Preloading a lazy-loaded hero.** The fix is removing `loading="lazy"` and adding `fetchpriority="high"`; a preload on top works around the attribute and leaves the cause in the markup.
- ❌ **A generic checklist.** "Minify CSS, use a CDN, enable compression" with no element, URL or number from the report.
- ❌ **"Fixed" after one better run.** Run-to-run variance, a different device or throttling, or a different Lighthouse version can move the score as much as the change did.
