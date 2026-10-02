# deck-builder — design reference

## Color palette principles

A presentation palette needs five roles. If the user gives you fewer than five colors, derive the missing ones following these rules:

| Role | Where it's used | Picking rule |
|---|---|---|
| **primary** | Title bars, section dividers, big-number captions | The user's brand colour, or the dominant colour in their material |
| **secondary** | Sparingly — second-tier emphasis, alt charts | Analogous or complementary to primary; ~30° apart on the wheel |
| **accent** | Highlight bars, the actual big numbers, quote bars | High-saturation pop colour; should NOT match background or primary |
| **background** | Slide background | Near-white (#FFFFFF or #F8F9FA) for most decks; near-black for dark-mode decks |
| **text** | Body text, bullet text | ≥ 4.5:1 contrast against background. Default `#222222` on white, `#EAEAEA` on dark |

### Hard rules

- **Contrast ≥ 4.5:1** between text and background (WCAG AA). If the user-supplied palette fails this, *substitute* and explain — don't ship an unreadable deck.
- **Never put primary text on primary background** — use white-on-primary or vice versa for title bars/section slides.
- **Accent appears on ≤ 20% of slides.** It's a pop colour, not a body colour.

### Preset palettes

These are bundled in [`templates/palettes.json`](templates/palettes.json) and selectable by name:

| Name | When to use |
|---|---|
| `corporate-blue` | Default for B2B / enterprise audiences when no brand colour is given |
| `monochrome` | When the deck needs to feel restrained / when content is sensitive |
| `vibrant` | Internal / sales / pitch decks — energetic |
| `dark-mode` | Engineering audiences who prefer dark, or for live demos |
| `editorial` | Long-form / read-ahead decks with lots of text |
| `forest` | Calm, nature-leaning — sustainability, long-horizon programmes |
| `sunset` | Warm, narrative-leaning — story-first sales and internal decks |

## Layout → content matching

The biggest deck-design mistake is "everything is a bulleted content slide". Use this mapping to pick the right layout for the content:

| Content shape | Right layout | Wrong layout |
|---|---|---|
| One key takeaway you want to land | `big_number` | `content` (gets lost in bullets) |
| A list of 2–6 related points | `content` | `two_column` (over-engineered) |
| A comparison (us vs. them, before vs. after) | `two_column` | `content` with sub-bullets |
| A pithy customer / SME quote | `quote` | `content` ("Customer says…") |
| 3+ comparable figures over time or category | `chart` | `content` with numbers in bullets |
| Row-and-column data, ≤ 12 rows | `table` | `two_column` faked with aligned bullets |
| An architecture / flow / screenshot | `image` | describing the diagram in prose |
| A topic break / new section | `section` | another title slide |
| First slide | `title` | jumping straight into `content` |
| Final slide with The Ask | `closing` | `content` titled "Thank you" |

## Per-audience density rules

How many bullets a slide can carry without falling apart, by audience:

| Audience | Bullets / slide | Words / bullet | Slide-title style |
|---|---|---|---|
| `exec` | 3 max | ≤ 8 | Assertion ("Postgres meets latency target") |
| `board` | 3 max | ≤ 6 | Outcome ("$24M ARR protected by Q3") |
| `technical` | 5–6 | ≤ 14 | Descriptive ok ("Migration approach") |
| `sales` | 3–4 | ≤ 10 | Benefit-led ("Cut close time by 40%") |
| `internal` | 4–5 | ≤ 12 | Topic ok ("Q3 priorities") |
| `investor` | 3–4 | ≤ 10 | Assertion + number where possible |
| `partner` | 3–4 | ≤ 10 | Mutual benefit ("Joint customers see X") |
| `customer` | 3–4 | ≤ 12 | Outcome for them ("You'll save…") |

## Slide-count budgets

| Audience / format | Slide count target | Hard upper bound |
|---|---|---|
| `exec` quick update (5 min) | 5 | 8 |
| `exec` decision review (15 min) | 8–10 | 12 |
| `board` quarterly (20 min) | 10 | 15 |
| `technical` design review (30 min) | 12–15 | 20 |
| `sales` first pitch (15 min) | 8 | 12 |
| `investor` Series-style | 10–12 | 15 |
| `internal` team alignment | 5–8 | 10 |

If the user's content can't fit in the upper bound, *say so* — recommend splitting into two decks rather than cramming.

## Speaker notes patterns

Every slide should have notes. The pattern that works:

1. **Hook sentence** — what the presenter opens with on this slide.
2. **Key emphasis** — which bullet/number to dwell on.
3. **Transition** — one sentence that flows into the next slide.

Speaker notes should be *what's not on the slide*, not a redundant copy.

## Common gotchas

- **Don't centre body text.** Centred bullets are harder to scan. Reserve centring for `big_number`, `quote`, and `title`/`closing` slides.
- **Don't underline links** — coloured-and-bold is the modern convention.
- **Don't use both italic and bold** in the same sentence for emphasis.
- **Don't mix serif and sans-serif** unless you really know what you're doing.
- **Slide numbers** — include them for decks > 10 slides; omit for short decks.

## Brand templates

A template is inherited, not imitated: `template` points the build at a `.pptx` or `.potx`, and
the deck is generated on that file's masters, theme fonts, theme colours, logos and slide size.
Sample slides shipped inside the template are dropped; its layouts are kept.

### The layout map

`layout_map` binds each logical layout to one of the template's layout names (or its index).
Discover them with `--list-layouts`. Matching is exact name first, then case-insensitive, then
substring — so `"content": "Title and Content"` and `"content": "title and content"` both hit.

| Logical layout | What to map it to | If unmapped |
|---|---|---|
| `title` | The template's title/cover layout | Built-in cover — **loses the brand**, always map it |
| `section` | Section header / divider | Built-in divider — always map it |
| `content` | Title and content / title and bullets | Built-in — always map it |
| `two_column` | Two content / comparison | Built-in two-column; acceptable |
| `closing` | Closing / thank-you / title-only | Built-in — always map it |
| `image` | Picture with caption (best), else title-only | Image drawn into the content area |
| `big_number`, `quote`, `table`, `chart` | Title-only | Drawn into the claimed content area; fine |

Placeholders are filled, not replaced — the run keeps the template's font, so the deck inherits
the brand's typography instead of Calibri. Placeholders left unfilled are deleted, so no
"Click to add text" ghosts survive. For `big_number`, `quote`, `table`, `chart` and `image`, the
largest empty body (or picture) placeholder is claimed for its rectangle and removed, so custom
content lands where the template intended content to go.

### Template gotchas

- **Slide size comes from the template.** `aspect` is ignored, with a warning. A 4:3 corporate
  master produces a 4:3 deck — tell the user rather than silently letting it look cramped.
- **Charts and tables are drawn, not templated.** They take palette colours, not theme colours.
  Supply brand hexes alongside the template so they match.
- **Slide numbers:** if the template's master already stamps them, the script does not add its
  own.
- **A template that fails to open** is a hard error, never a silent fall-back to the built-in
  design — a deck that quietly lost its branding is worse than a failed build.

## Charts

`chart` types: `column`, `bar`, `line`, `stacked_column`, `stacked_bar`, `pie`, `doughnut`.

| Question the slide answers | Type |
|---|---|
| How does this compare across categories? | `column` (≤ 7 categories) or `bar` (longer labels) |
| How has this moved over time? | `line` |
| What is the mix of a whole? | `pie`, and only with ≤ 5 slices |
| How does the mix change across categories? | `stacked_column` |

### Hard rules

- **Every chart carries a `takeaway`** — the sentence the audience should leave with, above the
  plot. A chart without one makes the audience do the analysis live.
- **Every chart carries a `source`.** No source means the number is unverifiable, which on a
  board deck means it is indefensible.
- **Never chart invented numbers.** If the user supplied three figures, chart three figures.
  A forecast is labelled a forecast, in the series name.
- **`null` is the right value for a gap.** Padding a short series with zeroes draws a cliff that
  didn't happen.
- **Pie charts cap at 5 slices.** More than that, use `bar` sorted descending.
- **One chart per slide.** Two charts is two slides, or a `two_column` with the takeaway split.

## Tables

- **≤ 12 data rows.** Past that it belongs in the appendix or an attached spreadsheet.
- **≤ 5 columns** at 16:9, ≤ 4 at 4:3. Wider than that and the font drops below readable.
- **Put the column the audience cares about last or first**, never buried in the middle.
- **Cells are values, not sentences.** A table cell running to two lines means the content is
  prose and wants a `content` slide.
- Font size auto-shrinks past 7 and past 10 rows; header row takes `primary`, body rows zebra
  against `#F2F4F8`.

## Images

- **Raster only.** `python-pptx` reads PNG/JPG/GIF/BMP/TIFF. SVG, EMF and PDF raise on import —
  export to PNG at 2× the slide size before building.
- **Relative paths resolve against the spec file**, not the working directory.
- `position: "left"` / `"right"` pairs the image with bullets on the other half;
  `"full"` (default) gives it the whole content area.
- A missing or unreadable image draws a bordered placeholder box naming the file, and warns.
  That box is a build artefact, never a deliverable — resolve it before the deck is presented.
