# Component spec: {component}

**Status:** draft · **Platform:** {web / iOS / Android} · **Token source:** {system name / brand.json / [proposed token]}
**Assumptions to confirm first:** {list, or "none"}

## Purpose and boundary

- **Use it for:** {one sentence}
- **Use something else when:** {one sentence, naming the other component}

## Anatomy

| # | Part | Required | Notes |
|---|---|---|---|
| 1 | {container} | yes | |

## Variants

| Axis | Values | When to use each |
|---|---|---|
| Emphasis | {primary / secondary / tertiary} | {} |
| Size | {sm / md / lg} | {} |

## States

| State | Visual change (by token, by part #) | Cursor | Announced by assistive tech |
|---|---|---|---|
| Default | | | |
| Hover | | | (nothing) |
| Focus | | | |
| Active / pressed | | | |
| Disabled | | | |
| Error | | | |
| Loading | | | |

## Tokens

| Part # | Property | Token | Notes |
|---|---|---|---|
| 1 | background | `{color.background.default}` | |

## Behaviour

- **Trigger and result:** {}
- **Overflow, truncation, wrapping:** {}
- **Responsive:** {}
- **Timing:** {debounce, auto-dismiss, animation}

## Content rules

- {label length budget, case, verb-first, never …}

## Accessibility

- **Native element / role:** {}
- **Accessible name:** {how it's computed}
- **States → ARIA:** {aria-invalid, aria-describedby, aria-busy, …}
- **Keyboard:** {key → action}
- **Focus:** {on open / close / error}
- **Contrast and size:** {text 4.5:1, non-text 3:1, target 24×24 CSS px}
- **Announcements:** {live region / status message}
- **WCAG 2.2 criteria:** {numbers and names from reference.md only}

## Do / don't

| ✅ Do | ❌ Don't | Why |
|---|---|---|
| {} | {} | {} |

## Open questions for engineering

| Question | Blocks |
|---|---|
| {} | {decision} |
