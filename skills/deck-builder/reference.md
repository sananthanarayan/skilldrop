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
| `accenture-purple` | Accenture-branded materials |
| `monochrome` | When the deck needs to feel restrained / when content is sensitive |
| `vibrant` | Internal / sales / pitch decks — energetic |
| `dark-mode` | Engineering audiences who prefer dark, or for live demos |
| `editorial` | Long-form / read-ahead decks with lots of text |

## Layout → content matching

The biggest deck-design mistake is "everything is a bulleted content slide". Use this mapping to pick the right layout for the content:

| Content shape | Right layout | Wrong layout |
|---|---|---|
| One key takeaway you want to land | `big_number` | `content` (gets lost in bullets) |
| A list of 2–6 related points | `content` | `two_column` (over-engineered) |
| A comparison (us vs. them, before vs. after) | `two_column` | `content` with sub-bullets |
| A pithy customer / SME quote | `quote` | `content` ("Customer says…") |
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
