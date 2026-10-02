# accessibility-audit reference — WCAG 2.2 AA catalog, AT map, severity, scanner gaps

Run the catalog as a lens, not a transcript. Report only what the UI fails or what the input can't verify. Citations use the SC number + name + level.

## The high-yield success criteria by POUR (WCAG 2.2, A + AA)

### Perceivable
- **1.1.1 Non-text Content [A]** — every image/icon/control has a text alternative; decorative images have empty alt; alt *says something useful* (not "image").
- **1.3.1 Info and Relationships [A]** — structure conveyed visually is in the markup: headings are `<h*>`, lists are lists, labels are programmatically associated, tables have headers.
- **1.3.2 Meaningful Sequence [A]** — DOM/reading order matches the intended order (CSS can lie; screen readers follow DOM).
- **1.3.5 Identify Input Purpose [AA]** — inputs use `autocomplete` for known data (name, email).
- **1.4.1 Use of Color [A]** — color is never the *only* way info is conveyed (errors, status, chart series, links in body text).
- **1.4.3 Contrast (Minimum) [AA]** — text ≥ 4.5:1; large text (≥24px, or ≥19px bold) ≥ 3:1.
- **1.4.4 Resize Text [AA]** / **1.4.10 Reflow [AA]** — usable at 200% text and 400% zoom with no loss of content/function, no horizontal scroll at 320px-equivalent.
- **1.4.11 Non-text Contrast [AA]** — UI components and graphical objects (input borders, icons, focus rings) ≥ 3:1.
- **1.4.12 Text Spacing [AA]** — no clipping when users override line/letter/word spacing.
- **1.4.13 Content on Hover/Focus [AA]** — tooltips/popovers are dismissable, hoverable, persistent.

### Operable
- **2.1.1 Keyboard [A]** — all functionality available from the keyboard.
- **2.1.2 No Keyboard Trap [A]** — focus can always move away.
- **2.1.4 Character Key Shortcuts [A]** — single-key shortcuts can be turned off/remapped.
- **2.4.3 Focus Order [A]** — tab order is logical and meaningful.
- **2.4.4 Link Purpose [A]** — link text makes sense (no bare "click here"/"read more" islands).
- **2.4.6 Headings and Labels [AA]** — descriptive; **2.4.7 Focus Visible [AA]** — a visible focus indicator on every focusable element.
- **2.4.11 Focus Not Obscured (Minimum) [AA, new in 2.2]** — focused element isn't hidden behind sticky headers/footers.
- **2.5.3 Label in Name [A]** — the accessible name contains the visible label text (voice control).
- **2.5.7 Dragging Movements [AA, 2.2]** — drag actions have a single-pointer alternative.
- **2.5.8 Target Size (Minimum) [AA, 2.2]** — targets ≥ 24×24 CSS px (or adequate spacing).

### Understandable
- **3.1.1 Language of Page [A]** — `lang` set.
- **3.2.1 On Focus / 3.2.2 On Input [A]** — focus/input doesn't trigger surprise context changes.
- **3.2.6 Consistent Help [A, 2.2]** — help mechanisms appear consistently.
- **3.3.1 Error Identification [A]** — errors are described in text, programmatically associated with their field.
- **3.3.2 Labels or Instructions [A]** — inputs have visible labels/instructions.
- **3.3.3 Error Suggestion [AA]** — fixable errors offer a suggestion.
- **3.3.7 Redundant Entry [A, 2.2]** / **3.3.8 Accessible Authentication (Minimum) [AA, 2.2]** — don't force re-entry; don't require a cognitive function test (e.g. solving a puzzle) with no alternative.

### Robust
- **4.1.2 Name, Role, Value [A]** — every UI component exposes a correct name, role, and state to AT (the #1 source of custom-widget failures).
- **4.1.3 Status Messages [AA]** — dynamic status (toasts, validation, live results) announced via `role="status"`/`aria-live` without moving focus.

## Affected-user / assistive-tech map (name the victim)

| Barrier | Who it blocks | Tech that hits it |
|---|---|---|
| No keyboard access / trap / no focus ring | motor-impaired, power users, anyone without a mouse | keyboard-only, switch control |
| Missing/wrong name-role-value, bad alt | blind, low-vision | VoiceOver, NVDA, JAWS |
| Low contrast, color-only signal | low-vision, color-blind, sunlight/poor-screen users | screen magnifier, everyone outdoors |
| No reflow / breaks at zoom | low-vision | 200–400% zoom, mobile |
| Surprise context change, complex auth | cognitive, low-literacy, anxiety | all |
| Tiny targets, drag-only | motor, tremor, touch | touch, switch, eye-tracking |
| Unannounced dynamic updates | blind | screen readers |

## Severity rubric (by task-completion impact)

- 🟥 **blocker** — a group cannot complete the core task at all.
- 🟧 **major** — significant barrier; a painful or non-obvious workaround exists.
- 🟨 **minor** — friction or confusion, task still completable.
- ⚪ **nit** — best practice / polish.

Calibrate: a keyboard trap on the only submit path is 🟥; `alt` slightly verbose is ⚪. If everything is 🟥, recheck against "can the task be completed?"

## What automated scanners catch vs miss (tag findings [auto] / [manual])

**Caught by axe/Lighthouse [auto]** (~30–40% of issues): missing alt attribute, missing form label, low text contrast (computed), missing `lang`, duplicate IDs, ARIA attribute misuse, empty buttons/links, missing document title.

**Human + AT only [manual]** (the majority): alt-text *quality*, label *accuracy* (right label on right field), logical focus *order*, meaningful reading sequence, keyboard *operability* of custom widgets, focus *visibility* in practice, error-recovery *usability*, whether color is the *only* signal, reflow at zoom, sensible heading *outline*, live-region *announcements* firing correctly, whether a context change is *surprising*. These don't stay fixed without a recurring manual pass — say so.
