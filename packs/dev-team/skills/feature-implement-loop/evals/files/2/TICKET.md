# LIB-88: Late fees for overdue items

As a circulation desk volunteer, I want the system to work out the late fee when an item is
checked in, so every patron is charged the same way.

Constraint: the desk laptops are locked down. Python 3.10, standard library only - nothing can
be pip-installed.

## Acceptance criteria

1. Fee = daily rate x chargeable days late. Daily rates: book $0.25, DVD $1.00.
2. Sundays, and the dates listed in closures.csv, are not chargeable days.
3. An item returned on or before its due date is charged $0.00.
4. The fee for one item is capped at its replacement cost or $10.00, whichever is lower.
5. Patrons with a junior card (card type "junior") are never charged.

## Worked example (from the desk)

A book due Friday 2026-03-06 and returned Wednesday 2026-03-11 is 5 days late:
5 x $0.25 = $1.25.
