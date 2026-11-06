# design-system-spec — reference

## WCAG 2.2 criteria this skill cites

Cite only these, by number and name. If a concern isn't covered here, describe it in plain words without a criterion number. Level is the conformance level the criterion belongs to.

| # | Name | Level | What it means for a component spec |
|---|---|---|---|
| 1.3.1 | Info and Relationships | A | Structure shown visually (label ↔ field, group ↔ options) is also in the markup: `<label for>`, `<fieldset>`/`<legend>`, `aria-describedby` for helper text. |
| 1.4.1 | Use of Color | A | Colour isn't the only signal for a state. An error state adds an icon or text, not just a red border. |
| 1.4.3 | Contrast (Minimum) | AA | Text at least 4.5:1 against its background; large text at least 3:1. |
| 1.4.11 | Non-text Contrast | AA | Visual information needed to identify UI components and their states (borders of inputs, icons, focus indicators) at least 3:1 against adjacent colours. |
| 1.4.12 | Text Spacing | AA | The component doesn't clip or overlap content when users increase line, paragraph, letter and word spacing. Don't fix heights on text containers. |
| 1.4.13 | Content on Hover or Focus | AA | Tooltips and popovers shown on hover or focus can be dismissed without moving the pointer (usually Esc), can be hovered themselves, and stay until dismissed or no longer relevant. |
| 2.1.1 | Keyboard | A | Everything works from a keyboard. |
| 2.1.2 | No Keyboard Trap | A | Focus can always leave the component with the keyboard. A modal dialog holds focus inside it by design, and Esc or a close button lets the user out. |
| 2.2.1 | Timing Adjustable | A | Content that disappears on a timer (auto-dismissing toasts that carry information or actions) needs a way to turn off, adjust or extend the time, unless an exception applies. |
| 2.4.3 | Focus Order | A | Focus moves in an order that keeps meaning and operation intact. |
| 2.4.7 | Focus Visible | AA | The keyboard focus indicator is visible. |
| 2.4.11 | Focus Not Obscured (Minimum) | AA | A focused component is not entirely hidden by author-created content such as sticky headers, footers or non-modal overlays. New in 2.2. |
| 2.5.3 | Label in Name | A | The accessible name contains the visible label text, so voice-control users can say what they see. |
| 2.5.7 | Dragging Movements | AA | Anything done by dragging (sliders, reordering) can also be done with single-pointer actions without dragging. New in 2.2. |
| 2.5.8 | Target Size (Minimum) | AA | Pointer targets at least 24 by 24 CSS pixels, or spaced so a 24 px circle centred on each doesn't overlap another target, with exceptions (inline links in text, an equivalent control elsewhere, essential, user-agent controls). New in 2.2. |
| 3.2.1 | On Focus | A | Receiving focus doesn't trigger a change of context (no navigation or submit on focus). |
| 3.2.2 | On Input | A | Changing a setting doesn't change context unexpectedly unless the user was told beforehand. |
| 3.3.1 | Error Identification | A | An input error that is detected automatically identifies the item in error and describes the error in text. |
| 3.3.2 | Labels or Instructions | A | Inputs have labels or instructions. |
| 3.3.3 | Error Suggestion | AA | When a fix is known, the error message suggests it (unless that would compromise security). |
| 4.1.2 | Name, Role, Value | A | Every control exposes its name, role, states and values to assistive tech, and changes to them are announced. |
| 4.1.3 | Status Messages | AA | Status messages (saved, loading, n results, errors that don't move focus) are announced by assistive tech without receiving focus, for example through `role="status"` or `role="alert"`. |

**Not AA:** 2.4.13 Focus Appearance (a minimum size and contrast for the focus indicator) is level AAA in WCAG 2.2. A design system may adopt it as its own rule; say so, and don't present it as an AA requirement.

**Removed:** 4.1.1 Parsing is obsolete in WCAG 2.2. Don't cite it.

**Large text** in 1.4.3 means at least 18 point, or 14 point bold. On the web, that is roughly 24 CSS px regular or about 18.66 CSS px bold.

## Keyboard patterns by component

Follow the WAI-ARIA Authoring Practices Guide (APG) pattern for the component when one exists. Typical keys:

| Component | Native element first | Keys |
|---|---|---|
| Button | `<button>` | Enter and Space activate |
| Link | `<a href>` | Enter activates |
| Checkbox | `<input type="checkbox">` | Space toggles |
| Toggle / switch | `<button aria-pressed>` or `<input type="checkbox" role="switch">` | Space toggles (Enter too, for a button) |
| Radio group | `<input type="radio">` in a `<fieldset>` | Tab into the group, arrow keys move and select |
| Text field | `<input>` / `<textarea>` with `<label>` | Standard text editing; Enter submits the form for a single-line input |
| Select | `<select>` | Native behaviour; build a custom listbox or combobox only if `<select>` can't do the job |
| Tabs | APG Tabs pattern (`tablist`, `tab`, `tabpanel`) | Tab into the tab list, arrow keys between tabs, Tab into the panel |
| Modal dialog | `<dialog>` opened with `showModal()`, or `role="dialog"` with `aria-modal="true"` | Focus moves into the dialog on open, Tab cycles inside, Esc closes, focus returns to the trigger on close |
| Menu button | APG Menu Button pattern | Enter, Space or Down opens; arrow keys move; Esc closes and returns focus |
| Toast | `role="status"` (or `role="alert"` for urgent errors) | Doesn't take focus; any action in it must be reachable another way, or the toast stays until dismissed |

## Token naming

Specs name tokens; they never contain raw values. A common shape is `category.property.variant.state`:

- Colour: `color.background.default`, `color.text.subtle`, `color.border.focus`, `color.border.danger`
- Space: `space.100`, `space.200` (a scale, not pixel names)
- Size and shape: `size.target.min`, `radius.medium`, `border.width.default`
- Type: `font.body.md`, `font.label.sm`
- Motion: `motion.duration.short`, `motion.easing.standard`

Use the system's own names when they are given. When proposing a token, tag it `[proposed token]` and list it in open questions, because adding a token is a design system decision, not a component one.
