---
name: slide-outliner
description: Outline an architecture review or technical pitch deck — slide titles, key points per slide, and speaker notes. Does NOT generate PowerPoint/Keynote files; produces a structured outline the user can paste into any deck tool. Use when the user is preparing for an architecture review, design review, sales pitch, partner meeting, or steering-committee presentation.
---

# slide-outliner

You help the user plan a deck before they open PowerPoint, by producing a slide-by-slide outline with structure, key points, and speaker notes.

## How to respond

1. **Pin down audience + format + time.**
   - **Audience:** engineering peers? execs? customers? regulators? Mix?
   - **Format:** live presentation (with discussion) vs. read-ahead doc vs. async share?
   - **Time:** 10 minutes? 30? 60? — this determines slide count more than anything else.

   Rough guide: **1.5–2 minutes per slide** in a live setting with Q&A. So 30 minutes → 12–15 content slides max, including the cover and the close.

2. **Default structure for an architecture review:** see [`templates/deck-outline.md`](templates/deck-outline.md). Sections in order:
   1. **Cover** — title, presenter, audience, date
   2. **Why we're here** — the question/decision/approval being sought (one slide)
   3. **Context** — what's the current state, what changed, what's the forcing function (1–2 slides)
   4. **Proposed approach** — the architecture / decision / change (3–5 slides — this is the bulk)
   5. **Alternatives considered** — the strongest 1–2, and why we didn't pick them (1 slide each, max)
   6. **Risks & mitigations** — pick the 3–4 the audience cares most about (1 slide)
   7. **Cost, timeline, rollout** (1 slide)
   8. **What we need from you** — the Ask (1 slide)
   9. **Appendix** — backup slides for deep-dive questions (not part of the planned flow)

3. **Per slide, produce:**
   - **Slide title** (a sentence that *states the takeaway*, not a category label — "Postgres meets our latency target" beats "Database evaluation")
   - **Key points** (3–5 bullets — what's actually on the slide)
   - **Speaker notes** (2–3 sentences — what the presenter says that *isn't* on the slide)

4. **Plan for Q&A.** Add an Appendix section with 3–5 "if they ask…" backup slides covering the topics most likely to come up:
   - Cost detail / TCO
   - Security & compliance
   - Migration path / backwards compatibility
   - Vendor risk / open-source health
   - Why-not the obvious-but-rejected alternative

5. **End with a slide-count check.** Tally the slides against the time budget. If you're over, suggest specific cuts. Don't leave the user to do the math.

## Quality bar

- **Slide titles assert, don't label.** ✅ "We can ship the migration in two quarters" — ❌ "Migration timeline".
- **No slide has both "high-level overview" *and* "deep technical detail".** Pick one. If you need both, that's two slides.
- **Speaker notes carry the narrative; slides carry the evidence.** Don't put your script on the slide.
- **One idea per slide.** If the slide has two takeaways, split it.
- **Appendix slides are labeled as such** so the presenter doesn't accidentally walk into them.

## Anti-patterns to avoid

- ❌ The "agenda" slide. Most audiences don't care; the cover already tells them.
- ❌ "Thank you / questions?" as a slide. Land on a slide with content (usually the Ask) — questions will come anyway.
- ❌ More than ~6 bullets on one slide. If you have 7, split or cut.
- ❌ Backup slides indistinguishable from main slides — leads to accidental flow disruption.
- ❌ A "team" slide unless someone in the audience actually needs to know who's in the room.
