# Worked example: Northwind Logistics operations risk register

## Input given to the skill

> We're Northwind Logistics, three depots. I need a risk register for the operations
> committee on 1 October. Here's what came out of the workshop: the WMS vendor (one vendor,
> no exit plan), not enough drivers for peak, ransomware on the depot laptops (old OS, shared
> admin login), fuel prices, our ISO 9001 surveillance audit with two open non-conformities,
> the riverside depot flooding, route planning depending on one analyst (we've fixed that,
> a second analyst is trained), and customer addresses floating around in spreadsheets.
> Owners: Priya Shah (Head of Ops) for WMS and flooding, Tom Okafor (Fleet) for drivers and
> routing, Mei Lin (IT Security) for ransomware, Ana Ruiz (Finance Director) for fuel, Ben
> Hart (Quality) for ISO, Sam Doyle (Data Protection Lead) for the spreadsheets. 5x5 is fine.
> [followed by the controls and dates for each risk]

The scope (operations, 12-month horizon), the scale (default 5×5) and every owner, control
and date came from the user. The skill wrote each risk as cause, event and consequence, and
scored inherent and residual.

## The register

[`northwind-register.csv`](northwind-register.csv), eight rows. One row as written:

| Field | Value |
|---|---|
| id | R-003 |
| title | Ransomware on depot laptops |
| cause | Depot laptops run an unsupported OS build and staff share a local admin account |
| event | Ransomware encrypts depot laptops and the file share |
| consequence | Depot dispatch runs on paper for days and customer data may be exposed |
| owner | IT Security Lead (Mei Lin) |
| inherent | likelihood 4 × impact 5 = 20 (critical) |
| residual | likelihood 2 × impact 4 = 8 (medium) |
| treatment | reduce |
| controls | EDR on all endpoints; shared admin account removed; offline backups tested monthly |
| due_date / next_review | 2026-09-30 / 2026-10-10 |
| review_trigger | Any EDR detection on a depot device or a failed backup restore |

## Script check

Command:

```bash
python3 scripts/check_register.py examples/northwind-register.csv --as-of 2026-10-01 --top 5
```

Real output (exit code 0):

```text
Risk register check
  file:   examples/northwind-register.csv
  as of:  2026-10-01
  scale:  1-5 likelihood x 1-5 impact
  bands:  low 1-4, medium 5-9, high 10-16, critical 20-25
  rows:   8 read, 8 valid, 7 open

Errors (0)
  none

Warnings (2)
  - line 9 [R-008]: treatment is reduce but no controls are listed
  - line 9 [R-008]: treatment is reduce but residual equals inherent (9); the controls change nothing

Overdue (2)
  - line 4 [R-003]: treatment action overdue by 1 day(s) (due_date 2026-09-30), owner IT Security Lead (Mei Lin)
  - line 6 [R-005]: review overdue by 16 day(s) (next_review 2026-09-15), owner Quality Manager (Ben Hart)

Inherent heat map, open risks (rows = likelihood, columns = impact)
  L\I |   1   2   3   4   5
  -------------------------
    5 |   .   .   .   .   .
    4 |   .   .   .   1   1
    3 |   .   .   1   1   1
    2 |   .   .   .   2   .
    1 |   .   .   .   .   .
  low 0, medium 3, high 3, critical 1

Residual heat map, open risks (rows = likelihood, columns = impact)
  L\I |   1   2   3   4   5
  -------------------------
    5 |   .   .   .   .   .
    4 |   .   .   .   .   .
    3 |   .   .   2   1   .
    2 |   .   .   .   2   1
    1 |   .   .   .   1   .
  low 1, medium 4, high 2, critical 0

Top 5 open risks by residual score
  R-002  residual 12 (high), inherent 16  Driver shortage in peak season  [reduce, owner Fleet Manager (Tom Okafor)]
  R-001  residual 10 (high), inherent 15  Single warehouse management system vendor  [reduce, owner Head of Operations (Priya Shah)]
  R-004  residual 9 (medium), inherent 12  Fuel price spike  [transfer, owner Finance Director (Ana Ruiz)]
  R-008  residual 9 (medium), inherent 9  Customer data in shared spreadsheets  [reduce, owner Data Protection Lead (Sam Doyle)]
  R-003  residual 8 (medium), inherent 20  Ransomware on depot laptops  [reduce, owner IT Security Lead (Mei Lin)]

Result: PASS
```

## Summary handed to the committee

**Scale:** 5×5, likelihood over 12 months, impact on operations objectives. Low 1–4,
medium 5–9, high 10–16, critical 20–25.

**Residual heat map:** as printed by the script above. No critical residual risks; two high.

**Decisions needed (3).** Deciders are roles the user did not name; confirm them before the meeting.

1. **R-002 Driver shortage, residual 12 (high).** Approve a third agency contract or accept
   the penalty exposure on the two retail contracts for peak. *Decider: Operations Director.*
2. **R-001 WMS vendor, residual 10 (high).** Approve budget to test the exit plan with a
   second vendor before year end, or accept single-vendor exposure for another year.
   *Decider: CFO.*
3. **R-008 Customer data in spreadsheets, residual 9.** No controls are listed and the
   residual equals the inherent score, so nothing is reducing it yet. Agree a control
   (for example, planning inside the WMS with exports switched off) and a date.
   *Decider: Sam Doyle with the Head of Operations.*

**Overdue (2):**

- R-003 ransomware actions were due 30 September, one day ago. Mei Lin to confirm whether
  the shared admin account removal is complete.
- R-005 ISO 9001 review was due 15 September. Ben Hart to rescore before the surveillance visit.

**Not raised:** R-006 flooding is accepted at residual 8 (medium) by its owner, which is
within her authority; R-007 is closed and stays in the register as history.

*This register prepares material for the operations committee and the risk owners to review.
It is not audit or legal advice.*
