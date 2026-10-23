# Worked example: a weekly support review becomes a six-slide deck

## Input given to the skill

> Can you turn support-weekly-input.md into slides? I'm presenting it at the ops review on
> Thursday. The Notes: line is what I'll say, not slide text.

The source is [`support-weekly-input.md`](support-weekly-input.md), with its chart
[`tickets-by-week.png`](tickets-by-week.png) next to it. It has front matter, four `##`
sections, a right-aligned table, an image, a `Notes:` paragraph, a long "Follow-ups" section
with two `###` groups and nested bullets, and an HTML notes comment at the end.

---

## What the agent did

**First run, to see what doesn't convert:**

```
$ python3 scripts/md_to_pptx.py support-weekly-input.md -o support-weekly.pptx
WARN line 1: YAML front matter dropped (lines 1-4); used on the title slide: title, date
WARN line 15: paragraph starting "Notes:" stays on the slide as text; wrap it in <!-- notes: ... --> to make it speaker notes
WARN line 30: "Follow-ups" did not fit on one slide; split into 2 slides (5-6) at a text boundary, text kept at full size
wrote support-weekly.pptx (6 slides, 1 of them continued, 1 table, 1 image, speaker notes on 1; 16:9; brand: no)
```

**Fixed the source in a copy.** The user said the `Notes:` line is what they'll say, so it
becomes a notes comment. Nothing else changed:

```diff
- Notes: lead with the backlog, it's the number the ops director watches.
+ <!-- notes: lead with the backlog, it's the number the ops director watches. -->
```

**Second run:**

```
$ python3 scripts/md_to_pptx.py support-weekly-fixed.md -o support-weekly.pptx
WARN line 1: YAML front matter dropped (lines 1-4); used on the title slide: title, date
WARN line 30: "Follow-ups" did not fit on one slide; split into 2 slides (5-6) at a text boundary, text kept at full size
wrote support-weekly.pptx (6 slides, 1 of them continued, 1 table, 1 image, speaker notes on 2; 16:9; brand: no)
  checked: 35 XML parts parse, 34 relationships resolve, every part has a content type
   1. Kestrel Support: weekly review [title]
   2. This week [notes]
   3. Tickets by week [image]
   4. Queue health [table]
   5. Follow-ups
   6. Follow-ups (continued) [notes]
2 warning(s): the items above were dropped, split or changed; tell the user before sharing
```

The outline matches the four `##` headings, plus one continued slide. The front matter warning
is expected: its title and date are on the title slide. The split kept the text at 20 pt. The
"Carried over" group and the first two "New" items are on slide 5, and the last two items are
on slide 6.

**Read both notes.** Slide 2's note is presenter guidance. Slide 6's note says *"Ana's request
for an engineer is not approved yet; don't promise it in the room."* That is fine to present
from, but anyone the file is forwarded to can read it.

**Checked it opens.** Microsoft PowerPoint for Mac 16.114 (2026-10-20) opened the file with no
repair prompt and counted six slides. A Quick Look thumbnail of each slide showed the table
with a shaded header and right-aligned numbers, and the chart centred under its title.

---

## Reply to the user

> Here's the deck: `support-weekly.pptx`, 6 slides (title, then This week, Tickets by week,
> Queue health, and Follow-ups over two slides). Follow-ups was too long for one slide, so it
> continues on slide 6 at full text size rather than shrinking.
>
> Your "Notes:" line is now the speaker note on slide 2. **Before you send the file to anyone:**
> slide 6's speaker note says Ana's engineer request isn't approved and not to promise it. It
> travels with the deck, so delete it from the notes pane if the deck goes beyond the room.
