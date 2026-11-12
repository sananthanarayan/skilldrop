# PRD excerpt: nurse shift swaps

St Aldric Hospital (invented), nursing workforce team. Web rostering system only; a mobile app is a
later project and not part of this work.

## Problem

Nurses arrange shift swaps by text message and a paper book on each ward. Managers find out late,
wards end up short, and nobody can tell afterwards who worked which shift.

## What we want

1. A nurse can offer one of their rostered shifts for swap, and see shifts others have offered.
2. A nurse can request to take an offered shift, giving one of their own shifts in exchange or
   taking it as an extra shift.
3. Manager approval is required for all swaps before the roster changes.
4. The system blocks any swap that would take a nurse over 48 hours of work in any rolling 7-day
   period (working-time rule). Example: a nurse on 40 hours who picks up a 12-hour shift would be
   at 50 hours, which is allowed.
5. A swap is only allowed between nurses of the same grade, or from a higher grade to cover a lower
   one; never a lower grade covering a higher one.
6. When a swap is approved, both nurses and the ward manager get a notification in the rostering
   system.
7. Extra shifts picked up through swaps are paid as overtime, and the overtime should flow
   automatically into the payroll export.
8. Every swap (offered, requested, approved, rejected) is kept in an audit history that the ward
   manager can view.

## Extract from the staff agreement (section 9.4)

"Swaps between nurses of the same grade working on the same ward do not require manager approval.
The ward manager must be notified of the swap before the first affected shift starts."

## Constraints

- The payroll export is frozen until January while payroll moves supplier. No changes to the export
  this quarter.
- Two developers. Planning wants the backlog in stories, no more than eight.
