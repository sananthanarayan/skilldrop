# Rubric: Slide Deck / Outline

Mirrors `slide-outliner` + `deck-builder` quality bars. Apply to either a finished deck (read titles + speaker notes) or an outline.

## Blockers
- **Audience is explicit or obvious from the deck.** Same content for execs vs engineers is a different deck — if you can't tell which one this is, that's the blocker.
- **Title slide isn't blank.** Real title + subtitle + presenter + date.
- **No surprise endings.** First and last slides match in style; the deck reads as one document, not two stitched together.
- **No fake numbers.** If a `big_number` slide reads "$24M ARR at risk" and that number isn't in the source brief, it's invented. Demand evidence or removal.

## Major
- **Slide count matches audience.** Exec deck >12 slides = major. Technical review <8 = thin. See `audience-profile`.
- **Bullet density matches audience.**
  - Exec: max 3 bullets, max ~8 words each.
  - Technical: up to 6 bullets if content really needs them.
  - More than that ⇒ flag.
- **Speaker notes exist for every slide.** Even one sentence. Without them the reviewer/co-presenter can't follow what's *between* the bullets.
- **Section dividers used sparingly.** At most one every 4–5 content slides.
- **Story arc visible from titles alone.** Read just the slide titles in order — do they tell the story? If not, the deck is a list, not a narrative.
- **Layout variety where it earns its keep.** `content` slide after `content` slide after `content` slide is unread by slide 4. Big numbers, quotes, two-column should appear when the content suits them — not as decoration.

## Minor
- **Palette is consistent.** No surprise colors that aren't in the palette.
- **Contrast is readable.** Light grey text on white = always flag.
- **Title style is consistent** (assertion / descriptive / outcome — pick one per deck).
- **No more than ~20 slides** for any audience. >20 ⇒ deck isn't the right format.
- **Ask slide present** (the closing slide with the explicit request — "Approve the $X budget by Y").

## Nits
- Punctuation consistency in titles (all sentence case vs all title case).
- Footer / page numbers consistent.
- Image alt text / accessibility (rare but worth flagging for board / regulated audiences).

## Anti-patterns to flag (always major)
- "Agenda" slide as slide 2 of a 6-slide exec deck. The deck *is* the agenda.
- Repeated bullets across slides (says the same thing 3 different ways).
- A deck that opens with "About us" before "the Ask" — for any audience that didn't request a company backgrounder.
- Animations or transitions referenced in notes — flag as a craft smell unless explicitly justified.

## What's working — look for
- A `big_number` slide using a real number from the source.
- A `quote` slide where the quote actually changes the reader's mind.
- A title that's an assertion ("X will cost $Y if we don't act") rather than a label ("X overview").
- Speaker notes that say *what to skip if running short on time*.
- A clear Ask in the final slide.
