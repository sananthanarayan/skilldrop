---
name: brand-kit
description: Capture a brand once as a reusable brand.json — logo files (and an on-dark version), colour roles as hex codes, heading and body fonts, voice, imagery rules, a PowerPoint template, contact details and the legal footer — plus a one-page BRAND.md, with text contrast checked and every value traced to where it came from. Use when the user wants decks, flyers or documents in their branding, says "use our brand", "here's our logo and colours", "set up our brand kit", or hands over brand guidelines.
---

# brand-kit

You turn whatever the user has about their brand (logo files, a guidelines PDF, a website, a
few hex codes, "we use green") into one `brand.json` that other skills build from:
[`deck-builder`](../deck-builder/SKILL.md) for PowerPoint decks and
[`marketing-flyer`](../marketing-flyer/SKILL.md) for flyers. Capturing the brand once means
nobody answers the same questions for every deck, and the deck and the flyer match.

## How to respond

1. **Ask for everything in one message, and take what they already gave.** Never ask for
   something the user already supplied.

   > To set up your brand kit, send whatever you have. Anything you skip I'll either take from
   > what you sent or leave for you to confirm:
   > 1. **Brand name**, and a tagline if you use one
   > 2. **Logo files.** The main logo, plus a white or light version for dark backgrounds if
   >    you have one. PNG is best; SVG works for flyers, but PowerPoint needs PNG.
   > 3. **Colours** as hex codes (`#0E5A46`), or a guidelines PDF or website I can read them from
   > 4. **Fonts** for headings and body text
   > 5. **Voice:** how you sound, and words you always or never use
   > 6. **Imagery:** the kind of photos or illustrations you use, and what to avoid
   > 7. **A PowerPoint template** (`.potx` or `.pptx`) if your company has one
   > 8. **Contact and legal:** website, email, phone, and any footer line such as "© 2026 …"

2. **Read the sources the user points to.** From a guidelines PDF or website, extract colour
   hex codes, font names, logo usage rules and voice. Tag every value with where it came from
   in `sources`: `[explicit]` when the source states it, `[inferred]` when you derived it (a
   colour sampled from the logo, a tone read from the About page). Never present an inferred
   value as the brand's own rule.

3. **Fill the five colour roles.** The roles are `primary` (main brand colour; slide title
   bars, flyer bands), `secondary` (supporting), `accent` (highlights, calls to action),
   `background` and `text`. If the user gave one or two colours, derive the rest and say which
   roles you filled. Usually `background` is white or a near-white tint of the primary,
   `text` is a near-black, and `secondary` is a lighter or darker step of the primary.

4. **Write the files** next to the logo files, so relative paths resolve:
   - `brand.json`, in the shape of [`templates/brand.json`](templates/brand.json). Leave a
     field out instead of guessing it.
   - `BRAND.md`: one page with the name, colour swatches as a table (role, hex, use), fonts,
     voice, imagery rules and logo rules, readable by a person who never opens the JSON.

5. **Check it.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_brand.py" ./brand/brand.json
   # Other IDEs (from the skill folder)
   python3 scripts/check_brand.py ./brand/brand.json
   ```

   It fails on a malformed hex code, text-on-background contrast below 4.5:1, a missing logo
   file or template. It warns when white text on the primary is hard to read, when the accent
   is too light for text, when a logo is SVG or EPS, or when fonts aren't set. Fix the
   failures. Report each warning with what it means for the deck or flyer.

6. **Hand off.** Tell the user the path to `brand.json` and that `deck-builder` and
   `marketing-flyer` will use it: `build_deck.py --brand brand.json`, or the flyer spec's
   `brand` field.

**Non-interactive runs** (subagent, CI, headless): never invent a brand colour, font or logo.
Use only what the input supplies, tag derived colours `[inferred]`, and list missing fields
at the top of the response. With no brand material at all, emit `BLOCKED: need at least a
brand name and either a logo file or one brand colour`.

## Useful references in this skill

- [`templates/brand.json`](templates/brand.json) — the full shape, with every field filled in for a sample brand
- [`scripts/check_brand.py`](scripts/check_brand.py) — the checker: hex format, contrast, logo files and formats, template
- [`examples/northwind-brand.md`](examples/northwind-brand.md) — worked example: a logo, two hex codes and a website become a brand kit

## Quality bar

- **Every colour is a hex code with a role.** "Our green" is not a brand colour; `#0E5A46` used for title bars is.
- **Text on background passes 4.5:1,** checked by the script rather than by eye.
- **Every value says where it came from,** and inferred values are marked as inferred.
- **Logo files are real paths that exist,** with a PNG for PowerPoint and an on-dark version when the brand has one.
- **Nothing is invented.** A field the user didn't supply and couldn't be read from their sources is left out and listed, not guessed.
- **BRAND.md fits on one page.** A person checks the brand from it without opening the JSON.

## When to use this skill

- ✅ Before the first branded deck or flyer, so both come out in the same brand
- ✅ The user hands over brand guidelines, a logo, or a website and asks for things "in our style"
- ✅ A brand has changed and the old `brand.json` needs updating

## When NOT to use this skill

- ❌ Designing a new brand from scratch: this captures a brand, it doesn't invent one
- ❌ Building the deck or flyer itself; use `deck-builder` or `marketing-flyer`
- ❌ A one-off document where the user only wants the default look

## Anti-patterns to avoid

- ❌ **Asking eight separate questions** instead of one message with everything.
- ❌ **Sampling a colour from a JPEG** and recording it as the official hex without the `[inferred]` tag.
- ❌ **Accepting an SVG logo for PowerPoint use** without saying a PNG is needed.
- ❌ **Picking a pale accent as the text colour** because it is "on brand". It fails contrast and nobody can read it.
- ❌ **Filling the voice section with adjectives** ("innovative, passionate"). Words to use and words to avoid are what a writer can act on.
