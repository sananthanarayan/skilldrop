# Worked example — login form component → severity-tagged audit

## Input (React component, verbatim)

```jsx
function LoginForm() {
  const [err, setErr] = useState(false);
  return (
    <div className="login">
      <div className="title" style={{fontSize: 22, fontWeight: 700}}>Sign in</div>
      <input type="text" placeholder="Email" style={{color: '#999'}} />
      <input type="password" placeholder="Password" />
      {err && <span style={{color: 'red'}}>✕</span>}
      <div className="btn" onClick={submit} style={{background:'#5b9', color:'#fff', padding:'6px 10px'}}>
        Log in
      </div>
      <span className="link" onClick={forgot}>Forgot?</span>
    </div>
  );
}
```

## Output

### Coverage note
Audited from component code: semantics, labels, roles, keyboard reachability, and contrast (from inline styles) are inspectable. Live focus-order and screen-reader output still need a real AT pass — flagged below.

### 🟥 Blockers

**A11Y-1 — Submit control is a `<div>`, unreachable and unoperable by keyboard** · `2.1.1 Keyboard [A]`, `4.1.2 Name, Role, Value [A]` · `[auto]`+`[manual]`
A `<div onClick>` is not in the tab order, doesn't fire on Enter/Space, and exposes no button role or name to AT.
Blocks: keyboard-only and screen-reader users from logging in at all — there is no other submit path.
Fix: use `<button type="submit">Log in</button>` inside a `<form onSubmit>`. Same for `Forgot?` → `<button>` (or `<a href>` if it navigates).

**A11Y-2 — Inputs have no programmatic label** · `3.3.2 Labels or Instructions [A]`, `1.3.1 Info and Relationships [A]`, `4.1.2 [A]` · `[auto]`
Placeholders are not labels: they vanish on input and many screen readers don't announce them reliably. A screen-reader user hears "edit text, blank".
Fix: add `<label htmlFor>` tied to each input (visible label preferred), or at minimum `aria-label`. Placeholders stay as hints, not the only label.

### 🟧 Major

**A11Y-3 — Error is conveyed by color and an icon glyph only, not associated with a field** · `1.4.1 Use of Color [A]`, `3.3.1 Error Identification [A]`, `4.1.3 Status Messages [AA]` · `[manual]`
A red `✕` with no text tells a blind or color-blind user nothing about what failed or which field. It's also not announced (no live region) and not linked to an input.
Blocks: blind users get no error info; color-blind users may miss the signal.
Fix: render text ("Incorrect email or password"), associate via `aria-describedby` on the relevant input, and put the message in `role="alert"` so it's announced.

**A11Y-4 — Email input text contrast fails AA** · `1.4.3 Contrast (Minimum) [AA]` · `[auto]`
`#999` on `#fff` = **2.85:1**, below the 4.5:1 minimum for normal text. Low-vision users can't read typed input.
Fix: darken to ≥ `#767676` (4.54:1) or darker.

### 🟨 Minor

**A11Y-5 — Submit button color contrast borderline / unverifiable focus ring** · `1.4.3 [AA]`, `2.4.7 Focus Visible [AA]` · `[auto]`+`[manual]`
White text `#fff` on `#5b9` (`#55bb99`) = **2.3:1** — fails 4.5:1 for the button label. Also, once it's a real `<button>`, confirm a visible focus indicator exists (can't verify from static code).
Fix: darken the button background (e.g. `#2e8b6f` ≈ 4.5:1) and ensure a visible `:focus-visible` outline.

### ⚪ Nits

**A11Y-6 — Title is a styled `<div>`, not a heading** · `1.3.1 [A]`, `2.4.6 [AA]`
Screen-reader users navigate by headings; a visual-only "Sign in" isn't in the outline.
Fix: `<h1>` (or appropriate level) instead of `<div className="title">`.

### What's solid
- `type="password"` is correct (masking + manager integration).
- Touch targets: padding gives the button adequate size once it's a real control — keep ≥ 24×24 (`2.5.8`).

### Must verify with live AT
- Focus **order** through the form (DOM order looks correct, but confirm).
- Screen-reader announcement of the error live region after a failed submit.
- Visible focus indicator on all controls (`2.4.7`) once they're focusable.
- Behavior at 400% zoom / reflow (`1.4.10`).

### Fix order
1. A11Y-1, A11Y-2 (blockers — nobody can log in via AT).
2. A11Y-3 (error semantics).
3. A11Y-4, A11Y-5 (contrast — quick CSS).
4. A11Y-6 (heading).
