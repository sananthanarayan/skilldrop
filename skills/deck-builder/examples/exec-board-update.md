# Example: Quarterly board update for a migration project

**Prompt the user gave:** *"Build me a board update deck for our migration project. We're 60% through, on track for Q1 close, $2.4M annualised infra savings so far, but we discovered two services need a schema rewrite and we now have a multi-region regulatory requirement. We're asking for a $620k budget overrun. Use corporate-blue palette."*

## Step 1 — Audience archetype lookup

Board update → use `audience-profile.board` archetype:

- **Slide count target:** 8–12
- **Bullet density:** ≤ 3 bullets/slide, ≤ 6 words/bullet
- **Required sections:** Cover, TL;DR, Strategic context, Financials, Risks, Ask
- **Tone:** Outcomes-led, business-first, big numbers welcome
- **Layouts to favour:** `big_number` (for the $2.4M and the $620k), `quote` (for credibility), `two_column` (for scope changes)

## Step 2 — Build the deck spec

```json
{
  "title": "ProjectX Migration — Board Update",
  "audience": "board",
  "palette": "corporate-blue",

  "slides": [
    {
      "layout": "title",
      "title": "ProjectX Migration",
      "subtitle": "Board update — Q3 FY26",
      "presenter": "S. Ananthanarayan",
      "date": "2026-09-15",
      "notes": "Open with: 'We're 60% through, on track, and asking for an overrun. Here's why it's still a good deal.'"
    },
    {
      "layout": "content",
      "title": "60% complete, zero customer incidents, on track for Q1 close",
      "bullets": [
        "8 of 14 services cut over",
        "p99 latency down 22% on migrated services",
        "Two services moved to phase 3 — schema rewrite"
      ],
      "notes": "Lead with zero incidents. Boards remember that more than any other number on this slide."
    },
    {
      "layout": "big_number",
      "title": "Annualised infra savings already realised",
      "number": "$2.4M",
      "caption": "From the 8 migrated services. Projected $5.8M at completion.",
      "notes": "Pause. Let the number land. Don't rush to the next slide."
    },
    {
      "layout": "two_column",
      "title": "What changed since the original plan",
      "left": {
        "title": "Original scope",
        "bullets": ["14 services migrated", "Single-region active", "Legacy DB decommissioned"]
      },
      "right": {
        "title": "Discovered in flight",
        "bullets": ["Schema rewrite for 2 services", "Multi-region (EU regulator)", "Auth refactor coupling"]
      },
      "notes": "Multi-region is a regulator change, not a planning miss. Say so explicitly."
    },
    {
      "layout": "quote",
      "quote": "The migration went smoother than any I've seen in 20 years.",
      "attribution": "VP Engineering, post phase-2 cut-over",
      "notes": "Optional, but de-risks the perception that we're behind."
    },
    {
      "layout": "content",
      "title": "Top 3 risks for the remaining 40%",
      "bullets": [
        "Schema rewrite: 6 weeks, dry-runs underway",
        "Auth refactor coupling: increases coordination overhead",
        "Holiday freeze: -4 calendar weeks"
      ],
      "notes": "Don't soften the risks. Boards trust presenters who name them."
    },
    {
      "layout": "big_number",
      "title": "Budget overrun we're requesting",
      "number": "$620k",
      "caption": "Covers schema rewrite + multi-region buildout. Payback: < 8 months.",
      "notes": "Position the overrun against the $5.8M projected savings — net positive within the same fiscal year."
    },
    {
      "layout": "closing",
      "title": "Approval requested: $620k FY26 budget overrun",
      "subtitle": "Decision needed by 2026-10-01 to keep Q1 close",
      "notes": "Land here. Take questions. Don't add a thank-you slide."
    }
  ]
}
```

## Step 3 — Generate

```bash
python3 scripts/build_deck.py /tmp/board-update.json -o ./out/board-update.pptx
```

## Step 4 — Hand-off to the user

> Generated `out/board-update.pptx` — 8 slides, corporate-blue palette. Two notes before you present:
>
> 1. **Verify the speaker notes** — I wrote them based on the content you gave me. Read through and adjust your phrasing.
> 2. **Replace the slide 5 quote** — I used a placeholder attribution. If you have the actual quote (and clearance to use it), paste it in slide 5.
>
> Want me to also produce an exec-summary one-pager from the same content?
