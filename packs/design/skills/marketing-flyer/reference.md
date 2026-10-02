# marketing-flyer reference

## Sizes

| `size` | Dimensions | Use |
|---|---|---|
| `letter` | 8.5 × 11 in | US noticeboards and handouts (default) |
| `a4` | 210 × 297 mm | Everywhere outside the US |
| `a5` | 148 × 210 mm | Leaflets, counter cards, two to a sheet |
| `square` | 1080 × 1080 px | Instagram and LinkedIn posts; export with `--png` |
| `story` | 1080 × 1920 px | Stories and phone screens; export with `--png` |

`"orientation": "landscape"` swaps width and height. The HTML sets `@page` to the exact size
with no margins and turns on exact colour printing, so a browser's *Print → Save as PDF* at
100% scale reproduces it. Home and office printers can't print to the edge. For a flyer
printed on a desk printer, keep important content at least 0.25 in (6 mm) from the edge,
which every layout already does except for the full-width image and band. For professional
printing with bleed, export the PDF and ask the printer for their bleed requirements.

## Layouts

| `layout` | Looks like | Use when |
|---|---|---|
| `hero` | Logo band, a full-width photo, then the copy | There's a strong photo, and the thing itself is the draw |
| `split` | A photo (or brand-colour block) down the left, copy on the right | The photo is portrait, or the copy is a list of points |
| `event` | Logo band, a large date block beside the headline, then photo and details | The date is the most important fact |
| `minimal` | Logo, headline, a rounded photo, copy on white | Offers and announcements where restraint reads as quality |

The first `details` entry is the date block in `event`; put the date there.

## Copy budgets

| Element | Budget | Why |
|---|---|---|
| Headline | ≤ 10 words | Read from across a room in two seconds |
| Subhead | One line | Who it's for, or why it's worth it |
| Points | ≤ 4, one line each | A flyer is scanned, not read |
| Body | ≤ 60 words, usually none | A paragraph is skipped on a noticeboard |
| Call to action | Exactly one, a verb | Two choices means neither gets made |

## Colour and contrast

- **Body text** must reach 4.5:1 against the background. The script refuses to build below that.
- **Header band and call to action:** the script prints white or the brand's text colour,
  whichever contrasts more with the fill. A pale accent therefore gets dark text. Don't
  override this.
- **Points' markers use the accent.** Keep the accent for shapes and highlights, not long text.

## Fonts

The HTML names the brand's fonts with a fallback, such as `'Georgia', serif`. A font the
viewer doesn't have installed falls back to the generic family, so the PDF uses whatever is
installed on the machine that printed it. For an exact match, export the PDF on a machine
that has the brand fonts installed.
