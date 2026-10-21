---
title: skilldrop, reviewed by its own skills
summary: The site's performance and accessibility, checked with the catalogue's own web-performance-review and accessibility-audit skills, the findings, and what was fixed. Pull requests are reviewed by pre-merge-review.
kind: explanation
---

# skilldrop, reviewed by its own skills

A catalogue that says its skills beat the plain agent should be willing to use them on itself.
On 21 October 2026 the site was checked with two of its own skills, and every finding was
fixed in the same change ([RFC-0061](../../docs/rfcs/0061-own-skills-on-own-site.md)). Pull
requests are also reviewed by a third, `pre-merge-review`, which posts its review to the
check's summary.

The two reviews below follow each skill's own format: the answer first, then the findings, then
what the review couldn't tell.

## Performance, with `web-performance-review`

**Whether real users have a problem can't be told yet.** The site has too few visitors for
Chrome's field data (CrUX) to report on it, so there is no p75 for LCP, INP or CLS. The lab
runs show no vital at risk. Across eight Lighthouse runs on six pages, LCP was 1.0–1.9 s
(good is 2.5 s or less), CLS was 0, and total blocking time was 0 ms.

1. **Docs pages: the code-colouring stylesheet blocked the first paint.** The LCP element on
   `docs/how-to/install.html` is its summary paragraph (`main#main > p.summary`). 84% of its
   1.29 s LCP was render delay, waiting on the Prism theme stylesheet from jsDelivr. The
   stylesheet now loads without blocking, and a `<noscript>` copy keeps code coloured with
   scripting off. On a local server, the median LCP of three runs fell to 0.9 s. That isn't
   comparable with the live site, so the live page is re-measured after the change deploys.
2. **Nothing else moves a vital.** The home page's LCP element is the nav wordmark
   (`a.nav__logo`, text), with 180 ms of TTFB and 397 ms of render delay in one run. The other
   findings were cache lifetimes and request chains, which save only lab load time and move
   no vital.

**What this review can't tell:**
- These were single lab runs, on Lighthouse 13.5.0's default mobile setting: a mid-range phone
  on slow 4G, with 4× CPU slowdown.
- A load run has no clicks, so it says nothing about INP. Total blocking time is only a proxy.
- Shifts after load, such as from scrolling, aren't seen.
- Field data, once there is enough traffic, decides.

## Accessibility, with `accessibility-audit`

**Coverage:** WCAG 2.2 AA, from the built HTML and CSS, plus Lighthouse's automated checks on
the home, start, catalogue, docs and skill pages. There was no live screen-reader pass. What
that needs is listed at the end. Lighthouse's accessibility score was 96 on the home and
catalogue pages before the fixes, and 100 on every checked page after.

### 🟧 Major

- **2.4.7 Focus Visible [AA]: on the home page's install tabs, three of the four tabs showed no
  focus.** The outline rule matched only the last radio button, so a keyboard-only user tabbing
  through "a role pack", "one skill" and "by hand" couldn't see where they were. `[manual]`
  **Fixed:** each tab's radio outlines its own label.

### 🟨 Minor

- **1.4.3 Contrast (Minimum) [AA]:** dark text `#0d0d0f` on the accent `#7c5cff` is **4.47:1**,
  against 4.5:1 needed. It appeared on the home page's selected tab, and on the catalogue's
  "heavy" tier badges, which are small uppercase text, 9.9 px. Low-vision users read these
  less easily. `[auto]` **Fixed:** the darker accent behind light text, 7.40:1 in the light
  theme and 8.57:1 in the dark one.
- **1.4.11 Non-text Contrast [AA]:** the search fields' borders were **1.27:1** (light) and
  **1.23:1** (dark) against their background, so a low-vision user could miss where to type.
  `[manual]` **Fixed:** a field-border colour of 3.71:1 in light and 3.80:1 in dark.

### What's solid

- Every page sets `lang`, and opens with a skip link to the main content.
- Animations stop when the reader asks for reduced motion.
- The tabs on the home and start pages are real radio buttons. They work from the keyboard and
  without JavaScript.
- Copy buttons carry an accessible name that says what they copy.
- Body and secondary text are at least 4.89:1 in both themes.

### Must verify with live assistive tech

- VoiceOver and NVDA on the search dialog: is focus moved into it and returned, and are results
  announced?
- Whether a tab change is announced, and the panel reached, with a screen reader.
- Reflow at 400% zoom on the catalogue and docs pages.
- Whether the theme toggle's pressed state is announced.

## Pull requests, with `pre-merge-review`

Each pull request in this repo gets a review from `pre-merge-review`, written to the check's
summary. It reports and never blocks: the required checks (lint, build, scan, CodeQL and the
smoke tests on three operating systems) decide whether a change can merge, and a person
decides whether it does.

The review needs the repo's `ANTHROPIC_API_KEY` secret, so it doesn't run on forks or on
Dependabot's pull requests.
