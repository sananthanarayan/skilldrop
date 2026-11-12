# Worked example: a 24-guest wedding dinner

Input → output oracle for `seating-plan`. Shows a first draft that broke three requests, a
conflict in the brief itself (the parents' fixed seats against "keep each household
together"), and how the reply names it instead of hiding it.

## Input

> We're seating our wedding dinner: a head table for four and two round tables of ten, so 24
> seats for 24 guests. The head table is us (Asha and Leo) plus Asha's mum Meera and Leo's dad
> Ian. Please keep each household together. Asha's grandmother Nani uses a wheelchair, and only
> the head table and table 1 are step-free. Priya and Dan must not be at the same table.
> Dietary: Nani, Omar and Ravi are vegetarian; Tess has a nut allergy. Guest list attached.

## The first draft, checked

Seating households in list order, with the parents fixed at the head table, gave:

```
FAIL must sit together but are split: Meera Verma (Head), Raj Verma (T1), Nani Verma (T1)
FAIL must sit together but are split: Ian Grant (Head), Sue Grant (T1), Kit Grant (T1)
FAIL Priya Nair and Dan Moore must be kept apart but both sit at table T1
3 failure(s)
```

Two of the three can't be fixed by moving people. Meera and Ian are fixed at the head table,
which seats four, and their households are three each. Keeping both households whole means
leaving the parents off the head table. That is the couple's choice, so the reply asks; it
doesn't decide. The third was a straight mistake: Dan moves to table 2 and Jon Park takes his
seat.

## The reply

**Every request is met except one that can't be, below.**

| Table | Guests |
|---|---|
| Head (step-free) | Asha Verma, Leo Grant, Meera Verma, Ian Grant |
| Table 1 (step-free) | Raj Verma, Nani Verma, Sue Grant, Kit Grant, Omar Diaz, Lia Diaz, Ben Cole, Ada Cole, Priya Nair, Jon Park |
| Table 2 | Tess Wu, Sam Wu, Nora Bell, Hal Bell, Zoe Lim, Max Lim, Eve Lim, Ravi Shah, Uma Shah, Dan Moore |

**One request can't hold as written.** With Meera and Ian at the head table, the Verma and
Grant households can't each sit together: the head table seats four. Raj and Nani, and Sue and
Kit, are together at table 1, the table nearest you. If you'd rather keep each household whole,
the head table becomes just the two of you, and Meera and Ian join their families at table 1.

**Caterer's list:** table 1, 2 vegetarian (Nani, Omar); table 2, 1 vegetarian (Ravi) and 1 nut
allergy (Tess).

Nani is at table 1, which is step-free. Priya and Dan are at different tables. The room plan
with names at each table is in `seating-plan.svg`.

## Why this is the oracle

- **Every rule is checked before the plan is shown,** and the draft's three failures never
  reach the couple.
- **A conflict in the brief is named, with the choice it needs.** A plain pass seats the parents
  at the head table and calls the households "together", or quietly drops the head-table
  request.
- **The reply is for the couple:** names at tables, the caterer's list, and the one decision
  that's theirs. No file formats, no tooling.
