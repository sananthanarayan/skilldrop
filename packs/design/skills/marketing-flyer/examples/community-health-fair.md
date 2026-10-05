# Worked example — an email about a health fair becomes a branded flyer

## Input given to the skill

> Can you make a flyer for our community health fair? Use our brand kit in ./brand/. It's
> Saturday 14 November, 10am to 2pm, at the Riverside Park pavilion, and it's free. We'll have
> free blood pressure and glucose checks, flu shots (no appointment), a kids' corner and some
> healthy cooking demos. Oh and a raffle. People should register at
> northwindhealth.example/fair so we know numbers. Letter size please, we'll print it at the office.

---

**Copy, fitted to a flyer.** Here is what I changed from your email:

- **Headline:** "Free community health fair" (5 words)
- **Subhead:** "Checkups, flu shots and healthy cooking — for the whole family"
- **Points (3):** free blood pressure and glucose checks · flu shots, no appointment needed ·
  kids' corner and healthy cooking demos. *The raffle is left off: four points is the most a
  flyer carries, and the other three bring people in. Say if you want it instead of the
  cooking demos.*
- **Call to action:** "Save your spot" → northwindhealth.example/fair
- **Layout:** `event`, because the date is the fact people need first

**Spec** (`flyer-spec.json`):

```json
{
  "brand": "./brand/brand.json",
  "size": "letter",
  "layout": "event",
  "headline": "Free community health fair",
  "subhead": "Checkups, flu shots and healthy cooking — for the whole family",
  "points": ["Free blood pressure and glucose checks", "Flu shots, no appointment needed", "Kids' corner and healthy cooking demos"],
  "details": [
    { "label": "When", "value": "Sat 14 Nov, 10am–2pm" },
    { "label": "Where", "value": "Riverside Park pavilion" },
    { "label": "Cost", "value": "Free" }
  ],
  "cta": { "text": "Save your spot", "url": "northwindhealth.example/fair" },
  "image": { "path": "./riverside-park.png", "alt": "Families at Riverside Park" },
  "footer": "© 2026 Northwind Health"
}
```

**Build:**

```
$ python3 scripts/build_flyer.py flyer-spec.json -o community-health-fair.html --brand ./brand/brand.json --pdf community-health-fair.pdf
wrote ./community-health-fair.html (event, letter; brand: yes; logo: yes)
  contrast: text 14.8:1 · band 8.2:1 · call to action 7.2:1
wrote ./community-health-fair.pdf
```

**The flyer:** Northwind's green band across the top with the white logo. A large amber date
block reading *Sat 14 Nov, 10am–2pm* sits beside the Georgia headline. Below are the park
photo, the three points with amber markers, Where and Cost, and an amber "Save your spot" panel
with the web address in dark text, because white on that amber would be hard to read. The
footer carries the website and the copyright line.

**Before you print:** read the date, time and place aloud against your email, open
northwindhealth.example/fair to check it works, and print one test copy.

---

**Why this is a good output:** every fact is copied from the email, and the one cut (the raffle)
is named and offered back instead of silently dropped. There's one call to action. The layout
puts the date first because that's what a passer-by needs. The contrast figures are reported,
and the panel text uses the colour that reads.
