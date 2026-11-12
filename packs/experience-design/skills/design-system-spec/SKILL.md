---
name: design-system-spec
description: Write a design system component spec — purpose, anatomy, variants, every state (default, hover, focus, active, disabled, error, loading), the design tokens each part uses by name, behaviour, content rules, accessibility (keyboard, focus order, ARIA role, contrast, target size) cited to WCAG 2.2 criteria, do/don't examples, and the open questions engineering must answer. Use when the user wants a component spec, design system documentation, "spec out this button / modal / text field", a component's states and tokens, or a design-to-engineering hand-off for a component.
---

# design-system-spec

Writes the spec a designer and an engineer can both build a component from, so it behaves the same in every product that uses it. The unit is one component (button, text field, modal, tabs, toast). The spec covers what it is for, its parts, its variants, every state, the tokens that style it, how it behaves, what text goes in it, and how it works with a keyboard and a screen reader. Accessibility is part of the spec, not a later pass. Once the component is built, `accessibility-audit` checks the real thing. The component's strings come from `ux-writing`, and the colours and fonts behind the tokens come from the brand (`brand-kit`).

## How to respond

1. **Get the component and the system in one message.** Ask at most 2 questions, spent on the weakest of: *which component and where it's used* (screenshots, a Figma description, existing code, or a list of use cases), and *the token set* (token names from the system, or a `brand.json`). Default the platform to web. With no token set, propose token names in the system's likely shape and tag each `[proposed token]`.

2. **State the purpose and the boundary.** One sentence on what the component is for, and one on when to use something else: ✅ *"Use a toggle for a setting that takes effect immediately. Use a checkbox when the change waits for a Save button."* A component without a boundary gets used for everything and grows variants until nobody can maintain it.

3. **Draw the anatomy.** Number every part (container, label, icon, helper text, and so on) and say which parts are required and which optional. Use the same numbers in the token and state tables.

4. **Define variants on separate axes.** Keep *emphasis* (primary, secondary, tertiary), *size* (small, medium, large) and *type* (with icon, icon-only) as independent axes, not a flat list of 14 combinations. Every variant states when to use it. Cut any variant with no use case in the input; a variant "for later" is debt.

5. **Specify every state** in a table: default, hover, focus (keyboard), active/pressed, disabled, error (if it takes input), loading (if it triggers async work), plus selected/checked or read-only where they apply. For each state give the visual change *by token*, the cursor, and what assistive tech announces. Focus is never shown by colour change alone, and it never looks the same as hover. Disabled states say why the component is disabled (a hint or tooltip), or the spec explains why it isn't needed.

6. **Name tokens, never raw values.** ✅ *`color.border.focus`, `space.200`, `radius.medium`, `font.label.md`* — ❌ *`#2563EB`, `8px`*. A raw value in a component spec forks the system. If a needed token doesn't exist, propose one and list it in open questions. When the brand colours are known, check that each text and border pair meets the contrast minimums in [`reference.md`](reference.md), and flag any pair that fails.

7. **Write the behaviour and the content rules.** Behaviour: what triggers the component, what it does, what happens on overflow, truncation, wrapping, and different screen widths, and its timing (debounce, auto-dismiss). Content rules: label length budget, case, verb-first for actions, what may never appear (e.g. no punctuation in button labels). Exact strings for the product come from `ux-writing`; the spec sets the rules.

8. **Write the accessibility section** from [`reference.md`](reference.md), and cite only the WCAG 2.2 criteria listed there:
   - **Keyboard:** every key and what it does (Tab, Shift+Tab, Enter, Space, Esc, arrow keys), matching the WAI-ARIA Authoring Practices pattern for that component when one exists.
   - **Focus order and management:** where focus goes on open, on close, and after an error, and that it is never trapped except inside a modal dialog that can be closed with Esc.
   - **Role and name:** the native element first (`<button>`, `<input>`, `<dialog>`), ARIA only when no native element fits. Say how the accessible name is computed and which states map to ARIA attributes (`aria-expanded`, `aria-invalid`, `aria-describedby`).
   - **Contrast and size:** text 4.5:1 (3:1 for large text); borders, icons and focus indicators 3:1 against their background; pointer target at least 24×24 CSS px or spaced to meet 2.5.8.
   - **Announcements:** errors, loading and success that don't move focus are announced through a live region or status message.

9. **Add do/don't pairs** for the 3–5 misuses most likely in the input's context, each with a one-line reason. ✅/❌ side by side.

10. **Emit with [`templates/component-spec.md`](templates/component-spec.md)** in one message: purpose and boundary, anatomy, variants, state table, token table, behaviour, content rules, accessibility, do/don't, and **open questions for engineering** (each with the decision it blocks: framework constraints, animation, controlled vs uncontrolled, how the error state is set). Hand-off: after build, run `accessibility-audit` on the component. See [`examples/text-field-spec.md`](examples/text-field-spec.md).

**Non-interactive runs** (subagent, CI, headless): a missing token set becomes `[proposed token]` names, and missing use cases become an `[assumption]` line at the top. If the component can't be identified from the input, emit `BLOCKED: need the component and where it is used`.

## Useful references in this skill

- [`reference.md`](reference.md) — the WCAG 2.2 criteria this skill cites (checked list), contrast and target size figures, keyboard patterns by component, token naming
- [`templates/component-spec.md`](templates/component-spec.md) — the spec skeleton with anatomy, variant, state, token and accessibility tables
- [`examples/text-field-spec.md`](examples/text-field-spec.md) — worked example: a text field with async validation, every state and its tokens

## Quality bar

- **Purpose and boundary are stated**, including when to use a different component.
- **Anatomy parts are numbered** and the numbers are reused in the state and token tables.
- **Variants sit on independent axes**, each with a use case. No speculative variants.
- **Every applicable state is specified**, including focus, disabled, error and loading. Focus differs from hover and isn't shown by colour alone.
- **Tokens are named, never raw values.** Proposed tokens are tagged and listed as open questions.
- **Accessibility covers keyboard, focus, role and name, contrast and announcements**, and every WCAG citation is one from the reference list with the right number and name.
- **Open questions for engineering each name the decision they block.**
- **Nothing is invented.** Token names, brand values and platform constraints not in the input are tagged `[proposed token]` or `[assumption]`.

## When to use this skill

- ✅ Documenting a new or existing component for a design system
- ✅ A design-to-engineering hand-off for one component
- ✅ Reconciling a component that behaves differently in three products
- ✅ Adding a state (loading, error) or a variant to an existing component

## When NOT to use this skill

- ❌ Auditing a built page or component against WCAG — that's `accessibility-audit`
- ❌ Writing the product's interface strings for a flow — that's `ux-writing`
- ❌ Capturing brand colours, fonts and logo — that's `brand-kit`
- ❌ Page-level structure or navigation — that's `information-architecture`

## Anti-patterns to avoid

- ❌ **Hex codes in the spec.** `#2563EB` is right until the rebrand, then wrong in 40 places.
- ❌ **The happy-path spec.** Default and hover only; engineering invents error, loading and disabled, three different ways.
- ❌ **Focus = hover.** A focus style that matches hover gives keyboard users no way to tell focus apart from where the mouse is.
- ❌ **`div` with a click handler.** No keyboard support, no role, no name. Specify the native element.
- ❌ **ARIA as decoration.** `role="button"` on a `<button>`, or `aria-label` that contradicts the visible label.
- ❌ **Disabled with no reason.** A greyed-out Save button with no hint leaves the user stuck.
- ❌ **Variant explosion.** "Primary-large-icon-left-destructive" as a named variant; use axes.
- ❌ **Citing WCAG from memory.** A wrong criterion number undermines the whole accessibility section. Cite only what the reference lists.
