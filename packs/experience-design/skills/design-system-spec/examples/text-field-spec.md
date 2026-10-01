# Worked example — a text field with async validation

## Input given to the skill

> Spec our text field for the Northwind design system. Used in sign-up (username, which we check
> for availability as you type), settings forms, and checkout. Today each product has its own and
> they look different. Our tokens: `color.text.default`, `color.text.subtle`, `color.text.danger`,
> `color.border.default`, `color.border.hover`, `color.border.focus`, `color.border.danger`,
> `color.background.input`, `color.background.disabled`, `space.100`, `space.200`, `radius.small`,
> `font.body.md`, `font.label.md`, `font.helper.sm`. Web, React.

## Output

# Component spec: Text field

**Status:** draft · **Platform:** web (React) · **Token source:** Northwind tokens, plus two `[proposed token]`s
**Assumptions to confirm first:** availability checks call an API that answers in under 2 seconds, and fields are single-line (multi-line is a separate textarea component).

### Purpose and boundary

- **Use it for:** short free-text input of one line: names, usernames, email, card number.
- **Use something else when:** the answer is one of a known set (select or radio group), it's a date (date picker), or it's more than one line (textarea).

### Anatomy

| # | Part | Required | Notes |
|---|---|---|---|
| 1 | Label | yes | Always visible, above the input. Never replaced by placeholder. |
| 2 | Input container | yes | Border and background |
| 3 | Input text | yes | |
| 4 | Helper text | optional | Format or reason we ask. Replaced by the error message in the error state. |
| 5 | Error message | in error state | Icon + text |
| 6 | Status indicator | optional | Spinner (loading) or check (valid), at the input's end |

### Variants

| Axis | Values | When to use each |
|---|---|---|
| Size | md (default), sm | sm only in dense tables and filters; md everywhere else |
| Width | full, fixed to expected length | Fixed width for known-length data (postcode, CVC) so the size hints at the answer |

No "outlined/filled" style variant: one style across products is the point of the spec.

### States

| State | Visual change (by token, by part #) | Cursor | Announced by assistive tech |
|---|---|---|---|
| Default | 2 border `color.border.default`, background `color.background.input`; 1 `color.text.default`; 4 `color.text.subtle` | text | Label, then helper text (via `aria-describedby`) |
| Hover | 2 border `color.border.hover` | text | nothing |
| Focus | 2 border `color.border.focus` plus a focus ring `[proposed token: border.width.focus]` outside the border | text | Same as default |
| Filled | No change from default | text | Label and value |
| Disabled | 2 background `color.background.disabled`; 3 `color.text.subtle`; helper text says why it's disabled | not-allowed | Label, value, "dimmed" or "unavailable" (from `disabled`) |
| Read-only | 2 border removed, value shown as text | default | Label, value, "read only" |
| Error | 2 border `color.border.danger`; 5 shown with icon in `color.text.danger`; 4 hidden | text | Label, value, "invalid", then the error text |
| Loading | 6 spinner at the end of 2; input stays editable | text | "Checking availability" in a status region, once per check |
| Valid (async only) | 6 check icon, colour `color.text.default` (not green alone) | text | "Username available" in the status region |

Focus differs from hover by the added ring, not by colour alone.

### Tokens

| Part # | Property | Token | Notes |
|---|---|---|---|
| 1 | type | `font.label.md` | |
| 1 | colour | `color.text.default` | |
| 2 | background | `color.background.input` | |
| 2 | border colour | `color.border.default` / `.hover` / `.focus` / `.danger` | by state |
| 2 | radius | `radius.small` | |
| 2 | padding | `space.100` vertical, `space.200` horizontal | |
| 2 | min height | `[proposed token: size.target.min]` | Must meet the 24×24 CSS px target minimum. Recommend larger for touch. |
| 3 | type | `font.body.md` | |
| 4, 5 | type | `font.helper.sm` | |
| 1→2, 2→4 | gap | `space.100` | |

### Behaviour

- **Async check:** starts 400 ms after the last keystroke `[assumption]`; a newer keystroke cancels the pending check. The result shows only for the current value.
- **Validation timing:** format errors show on blur, not on every keystroke. Once a field is in error, it re-validates on input so the error clears as soon as it's fixed.
- **Overflow:** text scrolls horizontally inside the input; the label wraps, never truncates.
- **Responsive:** full width below the small breakpoint, whatever the width variant.
- **Submit:** Enter submits the parent form. On submit with errors, focus moves to the first field in error.

### Content rules

- Label: a noun, 1–4 words, sentence case, no colon, no "Enter your…".
- Helper text: one sentence, under 80 characters, says the format or why we ask.
- Error: what's wrong and how to fix it, naming the field. Exact strings come from `ux-writing`.
- Placeholder: off by default. If used, only an example value ("sam@northwind.example"), never the label or instructions.

### Accessibility

- **Native element / role:** `<input>` with a `<label for>`. No ARIA role needed.
- **Accessible name:** from the visible label, so it satisfies 2.5.3 Label in Name.
- **States → ARIA:** `aria-describedby` → helper text (default) or error message (error); `aria-invalid="true"` in error; `disabled` attribute for disabled; `readonly` for read-only. Required fields use `required` and a visible "(required)" or "(optional)" convention, picked once per form.
- **Keyboard:** standard text input; Tab and Shift+Tab move in and out, so there's no trap.
- **Focus:** stays in the field during async checks; after a failed submit, moves to the first invalid field.
- **Contrast and size:** label, value, helper and error text at least 4.5:1; the input border and the focus ring at least 3:1 against the background; target at least 24×24 CSS px.
- **Announcements:** async results ("Checking availability", "Username available", "Username taken") go to a `role="status"` region so they're announced without moving focus.
- **WCAG 2.2 criteria:** 1.3.1 Info and Relationships, 1.4.1 Use of Color, 1.4.3 Contrast (Minimum), 1.4.11 Non-text Contrast, 2.4.7 Focus Visible, 2.5.3 Label in Name, 2.5.8 Target Size (Minimum), 3.3.1 Error Identification, 3.3.2 Labels or Instructions, 3.3.3 Error Suggestion, 4.1.2 Name, Role, Value, 4.1.3 Status Messages.

### Do / don't

| ✅ Do | ❌ Don't | Why |
|---|---|---|
| Label above the field, always visible | Placeholder as the only label | It disappears on typing, and has weak contrast |
| Show format errors on blur | Show "Invalid email" after the first keystroke | Users get told off before they've finished |
| Fixed width for a 3-digit CVC | Full-width CVC field | Width hints at the expected answer |
| Error icon + text + red border | Red border alone | Colour alone fails users who can't see red |
| Explain a disabled field in its helper text | Grey out with no reason | The user can't fix what they can't see |

### Open questions for engineering

| Question | Blocks |
|---|---|
| Controlled, uncontrolled, or both? | The React API and how forms libraries integrate |
| Who owns the debounce and cancel: the component or the caller? | Whether the async state is a prop or internal |
| Is the 400 ms debounce acceptable for the username API's rate limits? | The behaviour timing |
| Can we add `border.width.focus` and `size.target.min` to the token set? | Focus and size tokens; otherwise raw values leak in |
| Does the error message render in the component or via a form-level slot? | Where `aria-describedby` points |

**Next:** once built, run `accessibility-audit` on the sign-up form that uses it.
