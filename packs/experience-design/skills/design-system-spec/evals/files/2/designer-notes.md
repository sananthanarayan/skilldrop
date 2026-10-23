# Dose stepper — designer notes (MedRound ward medication app, tablet)

Context: nurses use MedRound on shared ward tablets to record liquid doses given at the bedside. The dose stepper replaces a free-text field that produced typing errors (e.g. "50" entered for "5.0").

Anatomy as drawn:
- Label above the field ("Dose (mL)")
- Minus button, value field, plus button, in one row
- Unit suffix "mL" inside the field, right-aligned
- Helper text below ("Prescribed: 5 mL")
- Error text below, replaces helper text

Behaviour as drawn:
- Step 0.5 mL. Minimum 0.5 mL, maximum 10 mL (the largest syringe the wards stock).
- Nurses can also type a value directly.
- Minus is disabled at the minimum, plus is disabled at the maximum.
- If the entered dose differs from the prescribed dose, show a warning (not an error) and require a second tap on Confirm.

Visual:
- Plus/minus buttons are 20 × 20 px so the row fits the narrow MAR column. WCAG only asks for 44 px at AAA so 20 px is fine for AA.
- Field border uses `color.border.default`; on focus use `color.border.focus-strong`.
- Error text uses `color.text.error` (#E57373) on the white surface — checked, passes AA.
- Disabled buttons use `color.icon.disabled`.
- Warning uses `color.text.warning`.
