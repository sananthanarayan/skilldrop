# Example: Q3 partner QBR on the company's own PowerPoint template

**Prompt the user gave:** *"Make the Q3 QBR deck for Northwind. Use our corporate template at
`~/brand/acme-master.potx` — it's mandatory, marketing rejects anything else. 25 minutes, live,
with the partner's CTO and two of their architects in the room. Renewal rate went 88 → 91 → 94%
over the last three quarters, ticket volume is down 31%, and we want to land the co-sell
expansion ask. Brand colours are #0B3D6B and #E8A33D."*

## Step 1 — Setup block, answered in one pass

| Input | Value | How it was resolved |
|---|---|---|
| Content | Renewal trend, ticket volume, expansion ask | Supplied |
| Audience | `partner` | Stated ("partner's CTO and architects") |
| Format | Live, 25 min → 12–14 slides | Stated; slide count derived at ~2 min/slide |
| Aspect | From the template | `aspect` ignored — the `.potx` is 16:9 |
| Design | `~/brand/acme-master.potx` + brand hexes | Template for chrome, palette for charts |
| Embeds | Renewal trend (chart), SLA table | Three comparable figures ⇒ chart, not bullets |

The palette is still collected: the template does not colour charts, tables or big numbers.
`primary: #0B3D6B`, `accent: #E8A33D`; `secondary`, `background` and `text` derived per
[`reference.md`](../reference.md#color-palette-principles) and called out to the user.

## Step 2 — Read the template's layouts before writing the spec

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/build_deck.py" --list-layouts ~/brand/acme-master.potx
```

```
acme-master.potx — slide size 13.33in x 7.50in
  [0] Acme Cover
  [1] Acme Section Break
  [2] Acme Title and Body
  [3] Acme Two Column
  [4] Acme Statement
  [5] Acme Full Bleed Image
  [6] Blank
```

The names are the template's, not PowerPoint's defaults — which is exactly why the map is read
from the file rather than guessed.

## Step 3 — The deck spec

```json
{
  "title": "Northwind QBR — Q3 FY26",
  "audience": "partner",
  "template": "~/brand/acme-master.potx",
  "layout_map": {
    "title": "Acme Cover",
    "section": "Acme Section Break",
    "content": "Acme Title and Body",
    "two_column": "Acme Two Column",
    "big_number": "Acme Statement",
    "quote": "Acme Statement",
    "chart": "Acme Statement",
    "table": "Acme Statement",
    "image": "Acme Full Bleed Image",
    "closing": "Acme Statement"
  },
  "palette": {
    "primary": "#0B3D6B",
    "secondary": "#4A6E94",
    "accent": "#E8A33D",
    "background": "#FFFFFF",
    "text": "#222222"
  },
  "slides": [
    {
      "layout": "title",
      "title": "Northwind × Acme — Q3 business review",
      "subtitle": "Renewals, service quality, and the FY27 co-sell ask",
      "presenter": "Jane Roe, Partner Director",
      "date": "2026-09-30",
      "notes": "Thank them for the quarter before the first slide. Name the ask now so it isn't a surprise at slide 12."
    },
    {
      "layout": "chart",
      "title": "Renewal rate has climbed every quarter this year",
      "takeaway": "Three consecutive quarters of improvement — the joint success plan is what changed.",
      "chart": {
        "type": "line",
        "categories": ["Q1 FY26", "Q2 FY26", "Q3 FY26"],
        "series": [{ "name": "Renewal rate (%)", "values": [88, 91, 94] }],
        "number_format": "0\"%\""
      },
      "source": "Northwind CS dashboard, 30 Sep 2026",
      "notes": "Let them claim the win — ask their CTO what drove Q2. The answer is usually the thing to double down on in FY27."
    },
    {
      "layout": "big_number",
      "title": "Support load is down as adoption is up",
      "number": "-31%",
      "caption": "Ticket volume vs. Q3 FY25, on 2.4× the seat count",
      "notes": "The pairing is the point: more users, fewer tickets. Pause after saying it."
    },
    {
      "layout": "table",
      "title": "SLA performance against contract",
      "columns": ["Metric", "Contracted", "Q3 actual", "Status"],
      "rows": [
        ["Availability", "99.9%", "99.97%", "Met"],
        ["P1 response", "15 min", "9 min", "Met"],
        ["P1 resolution", "4 hrs", "3h 10m", "Met"],
        ["Change failure", "< 5%", "6.2%", "Missed"]
      ],
      "caption": "Change-failure remediation plan on the next slide.",
      "notes": "Do not skip the missed row. Naming it before they do is what makes the other three credible."
    },
    {
      "layout": "closing",
      "title": "Ask: co-sell motion for FY27, two named accounts each",
      "subtitle": "Kick-off 15 Oct, joint pipeline review monthly",
      "notes": "Land on the ask. Get the kick-off date agreed in the room, not in follow-up email."
    }
  ]
}
```

*(Abridged — the full deck is 13 slides; the four above are the ones that show the new layouts.)*

## Step 4 — Build

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/build_deck.py" /tmp/northwind-qbr.json -o ./out/northwind-qbr.pptx
```

```
template: dropped 2 sample slide(s), kept masters and layouts
wrote ./out/northwind-qbr.pptx (13 slides, template)
```

No warnings, so nothing to report. Had the SLA table's diagram been an `.svg`, the build would
have drawn a placeholder box and warned — which gets reported to the user with the path, not
quietly shipped.

## What the template bought

| Without the template | With it |
|---|---|
| Calibri, generated-looking cover | Acme's typeface, cover, and logo on every slide |
| Palette-coloured title bars | The master's own chrome |
| Marketing sends it back | Passes brand review unchanged |

The palette still did real work: the line chart, the `-31%`, and the table header are brand
colours because `palette` was collected *alongside* the template, not instead of it.
