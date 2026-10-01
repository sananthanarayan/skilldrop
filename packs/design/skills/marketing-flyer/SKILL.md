---
name: marketing-flyer
description: Generate a print-ready, on-brand marketing flyer — event, launch, open day, offer, hiring — as one self-contained HTML file (Letter, A4, A5, or square and story sizes for social) that saves to PDF, built from the user's own logo, colours, fonts and content, with one call to action, a short headline, contrast checked, and no invented dates, prices or contact details. Use when the user wants a flyer, poster, one-pager, handout, leaflet or event announcement "in our branding", or says "make a flyer for…".
---

# marketing-flyer

You make a flyer that looks like it came from the user's own team, because it's built from
their brand: their logo, their colours, their fonts, their words. The output is one HTML file
with the images embedded, sized for print, that saves to PDF from any browser. When a
`brand.json` from [`brand-kit`](../brand-kit/SKILL.md) exists, use it, and the flyer will match
the user's decks from [`deck-builder`](../deck-builder/SKILL.md).

## How to respond

1. **Ask for everything in one message.** Take what's already been given, and suggest
   defaults so the user can reply "go".

   > Before I build the flyer, send these. Anything you skip, I'll use the default shown:
   > 1. **Brand:** a `brand.json` from brand-kit, *or* your logo file (and a white version for
   >    dark backgrounds), brand colours as hex codes, and heading and body fonts.
   >    *Default: no brand, which looks generic, so please send at least a logo and one colour.*
   > 2. **What it's for, and who reads it:** an event, a launch, an offer, hiring, a service
   > 3. **The words:** a headline (ten words or fewer), a one-line subhead, up to four key
   >    points, and details such as date, time, place and price
   > 4. **One call to action:** what the reader should do, and the web address, phone or email for it.
   >    A QR code image too, if you have one.
   > 5. **Images:** a photo for the top of the flyer, if any, with a line describing it
   > 6. **Size:** `letter` · `a4` · `a5` · `square` (Instagram/LinkedIn) · `story` · and
   >    portrait or landscape. *Default: letter, portrait.*
   > 7. **Layout:** `hero` (photo across the top) · `split` (photo down one side) ·
   >    `event` (a big date block) · `minimal`. *Default: event when there's a date, otherwise hero.*

   **Content is the hard input.** Never invent a date, time, price, address, phone number,
   web address or statistic. If the user gave only a topic, ask for the details. A flyer with
   a wrong date is worse than no flyer.

2. **Write the copy to fit a flyer.** Rewrite long text into the flyer's shape and show the
   user what you changed:
   - A headline of ten words or fewer that names the thing, such as "Free community health
     fair", not "You're invited!".
   - A subhead that says who it's for, or why it's worth coming.
   - At most four points, each one line, so they can be read in passing.
   - Exactly **one** call to action, worded as a verb ("Save your spot", "Call to book"). Two
     calls to action means the reader does neither.

   Use the brand's voice from `brand.json` when it has one: words to use, words to avoid.

3. **Write the spec** in the shape of [`templates/flyer-spec.json`](templates/flyer-spec.json),
   with paths relative to the spec file.

4. **Build it.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/build_flyer.py" flyer-spec.json -o flyer.html --brand ./brand/brand.json --pdf flyer.pdf
   # Other IDEs (from the skill folder)
   python3 scripts/build_flyer.py flyer-spec.json -o flyer.html --brand ./brand/brand.json --pdf flyer.pdf
   ```

   `--pdf` and `--png` use a local Chrome or Chromium when one is installed. Without one, the
   user opens `flyer.html` and prints it to PDF at 100% scale with margins set to none.
   Use `--png` for the `square` and `story` sizes, which are posted as images.

5. **Read the output and every warning.** The script prints three contrast figures: text,
   the header band, and the call to action. It picks white or the brand's text colour on each
   filled band, whichever reads better. It warns about a long headline, more than four
   points, more than one call to action, a missing logo or image, and no brand. Fix what you
   can, and report the rest to the user with what it means.

6. **Tell the user how to check it before printing:** read every date, time and address
   aloud against the source, check the web address works, and print one test copy.

**Non-interactive runs** (subagent, CI, headless): missing *content* does not get a default.
Emit `BLOCKED: need the flyer's details: <what is missing>` and build nothing. Missing brand
falls back to defaults with an `[assumption]` line at the top; never make up a logo.

## Useful references in this skill

- [`reference.md`](reference.md) — sizes and print rules, layouts and when to use each, copy budgets, contrast
- [`templates/flyer-spec.json`](templates/flyer-spec.json) — the spec, every field shown
- [`scripts/build_flyer.py`](scripts/build_flyer.py) — the builder (stdlib only): HTML, plus PDF and PNG through headless Chrome
- [`examples/community-health-fair.md`](examples/community-health-fair.md) — worked example: an email from the user becomes a flyer spec and a branded flyer

## Quality bar

- **It is in the user's brand:** their logo, their colours as hex codes, their fonts. Default colours only when the user has no brand material, and then said out loud.
- **Every fact comes from the user.** Dates, times, places, prices and contact details are copied, not composed.
- **One call to action,** worded as a verb, with the address or number that makes it actionable.
- **A headline of ten words or fewer, at most four points.** Anything longer belongs on the linked page.
- **Text is readable everywhere:** body text at least 4.5:1 against the background, and the script's band and call-to-action figures reported.
- **The file is the whole flyer.** Images are embedded, with no links to local files that break when it's emailed.

## When to use this skill

- ✅ An event, a launch, an open day, an offer, a hiring drive, a service announcement
- ✅ A one-page handout or leaflet in the company's branding
- ✅ A square or story-sized image for social posts that matches the printed flyer

## When NOT to use this skill

- ❌ A slide deck; use `deck-builder`
- ❌ A multi-page brochure or a report, which this doesn't lay out
- ❌ Designing a brand from scratch; capture an existing one with `brand-kit`

## Anti-patterns to avoid

- ❌ **"You're invited!" as the headline.** Name the event, the offer or the product.
- ❌ **Three buttons** ("Register", "Learn more", "Follow us"). Pick the one action that matters.
- ❌ **Filling a missing date with "TBC"** or a plausible guess. Ask, or build nothing.
- ❌ **White text on a pale accent** because the brand's buttons are white. The script flips it; don't override it.
- ❌ **A paragraph of body copy.** No one reads a paragraph on a noticeboard.
- ❌ **Sending the HTML with images linked from the user's disk.** Always build with the script, which embeds them.
