# Story: staff discount at the till

Triaged and agreed 2026-11-02 (owner: Tobias Renk, retail product).

Staff can enter a percentage discount on a basket at the till.

## Acceptance criteria

1. `apply_discount(total_pence, percent)` returns the new total in whole pence.
2. The discount can never be more than 50%. A higher percent is treated as 50.
3. A negative percent is treated as 0.
4. Halves of a penny round up (e.g. 12.5p off becomes 13p off).
