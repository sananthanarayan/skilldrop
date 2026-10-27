# Worked example — a logo, two colours and a website become a brand kit

## Input given to the skill

> Set up our brand kit. Logo is `./brand/northwind-logo.png` and there's a white version
> `./brand/northwind-logo-white.png`. Our colours are `#0E5A46` and `#F2A541`. We use Georgia
> for headings. Website is northwindhealth.example.

---

**Wrote** `./brand/brand.json` and `./brand/BRAND.md`.

**Filled for you, please confirm:** `secondary` `#3D7F6B` (a lighter step of your green),
`background` `#FFFFFF` and `text` `#1F2A28` (near-black with a green cast). Voice is read
from your About page and tagged `[inferred]`.

**Not set (nothing supplied):** body font, tagline, phone, address, legal footer, PowerPoint
template. Tell me your body font; until then decks and flyers use their defaults.

```
$ python3 scripts/check_brand.py ./brand/brand.json
  text on background   14.79:1
  white on primary      8.17:1
WARN accent on background is 2.05:1 — use the accent for shapes and rules, not text
WARN fonts.body is not set; generators fall back to their defaults
OK: brand.json — 0 failure(s), 2 warning(s)
```

### BRAND.md

| Role | Hex | Use |
|---|---|---|
| primary | `#0E5A46` | Slide title bars, flyer header band, buttons |
| secondary | `#3D7F6B` | Charts, secondary panels |
| accent | `#F2A541` | Call to action, highlights; shapes and rules, never body text |
| background | `#FFFFFF` | Page and slide background |
| text | `#1F2A28` | Body text |

- **Fonts:** headings Georgia (from you); body font not set yet
- **Logo:** full colour on white; the white version on the green. Never the full-colour logo on the green.
- **Voice** `[inferred]`: warm and plain, short sentences. Says "members", not "patients".

---

**Why this is a good output:** it uses every fact the user gave and invents none. It fills only
the colour roles a deck needs, says which ones it filled, and leaves the tagline and legal
footer empty rather than making them up. The checker's figures show white titles on the
green will read, and its accent warning is carried into BRAND.md as "never body text".
