# Example: guest checkout, from PRD to Jira and back

Two runs on one PRD. First the user asks for Jira-ready issues from the PRD. Two weeks later
they ask whether the tracker still matches the doc.

Files:
- [`prd-guest-checkout.md`](prd-guest-checkout.md): a PRD in prd-draft's shape, with goals G1–G2
  and requirements R1–R7 (R7 is Won't have)
- [`guest-checkout-spec.json`](guest-checkout-spec.json): the issues spec written from the PRD
- [`tracker-after-two-weeks.csv`](tracker-after-two-weeks.csv): the Jira export two weeks later

## Run 1: PRD to issues

> "Turn this PRD into Jira epics and stories. Link each back to its section. The wiki copy is at
> https://wiki.northwind.example/checkout/prd-guest-checkout."

**Mapping, before writing the spec.** One epic per goal, one story per requirement:

| Doc section | Becomes | Why |
|---|---|---|
| G1 | Epic E1 "Checkout without an account" | Goal; R1–R3 map to it |
| G2 | Epic E2 "Support and safety for guest orders" | Goal; R4–R6 map to it |
| R1–R6 | Stories S1–S6 under their goal's epic | One testable requirement each; the acceptance criteria restate the requirement's observable behaviour |
| R7 | Nothing | Won't have. Listed under "Not created" so nobody adds it later by mistake |
| Non-goals, open question | Nothing | Not work. The open question about 3-D Secure goes back to the user as an unresolved dependency |

The spec is [`guest-checkout-spec.json`](guest-checkout-spec.json). Then:

```bash
python3 scripts/brief_sync.py export examples/guest-checkout-spec.json --target jira \
  --doc examples/prd-guest-checkout.md -o guest-checkout-jira.csv
```

Script output, unedited:

```text
wrote guest-checkout-jira.csv: 8 items (2 epics, 6 others)
```

First three rows of the CSV, unedited:

```csv
Issue Id,Parent Id,Issue Type,Summary,Description,Labels,Labels
1,,Epic,Checkout without an account,"Let first-time shoppers pay without creating an account. Goal: sign-up-step drop-off from 38% to under 20% within 4 weeks of launch.

Source: https://wiki.northwind.example/checkout/prd-guest-checkout#goals (G1)",guest-checkout,
2,,Epic,Support and safety for guest orders,"Guest orders can be found, screened and returned like account orders.

Source: https://wiki.northwind.example/checkout/prd-guest-checkout#goals (G2)",guest-checkout,
3,1,Story,Pay as a guest with email and delivery details,"As a first-time shopper, I can pay without creating an account, so I can buy in one sitting.

Acceptance criteria:
- Given a shopper with no account at checkout, when they choose Continue as guest, then they can pay after entering only an email address and delivery details
- Given a guest payment succeeds, then no account is created

Source: https://wiki.northwind.example/checkout/prd-guest-checkout#requirements (R1)",guest-checkout,checkout
```

The spec check catches mistakes before anything reaches the tracker. Here's the same spec with
five deliberate errors (a story with no criteria, a missing parent, a Won't-have source, a
section that isn't in the doc, a label with a space):

```text
spec has 5 problem(s):
  - S1: a story needs acceptance_criteria
  - S2: parent 'E9' is not an item in the spec
  - S3: source 'R7' is marked Won't have in the doc
  - S4: source 'R12' is not a section in the doc
  - S5: label 'guest checkout' has a space; Jira labels can't
```

The script exits 1 and writes nothing.

**What the user gets back:** the CSV, the mapping table above, and:

- **Import steps:** in Jira's CSV importer, map `Issue Id` and `Parent Id` so stories land under
  their epics, and map both `Labels` columns to Labels.
- **Not created:** R7 (Won't have), the three non-goals.
- **Unresolved:** the PRD's open question (does the PSP need an account ID for 3-D Secure on
  guest payments?) may add work to R1. No issue was created for it, because the doc doesn't
  define any.

## Run 2: drift, two weeks later

> "Here's the Jira export for guest checkout. Does it still match the PRD?"

```bash
python3 scripts/brief_sync.py drift --doc examples/prd-guest-checkout.md \
  --export examples/tracker-after-two-weeks.csv -o drift.md
```

Script output, unedited:

```markdown
# Drift: prd-guest-checkout.md vs tracker-after-two-weeks.csv

9 sections in the doc (6 need an issue, 1 marked Won't have) · 11 issues in the export (1 canceled or duplicate, ignored)
Sections are IDs matching `R\d+`.

| Drift | Count |
|---|---:|
| Doc sections with no issue | 1 |
| Issues with no doc section | 1 |
| Issues pointing at a section the doc doesn't have | 1 |
| Issues for a Won't-have requirement | 1 |

## Doc sections with no issue

- R3 (S): After paying, a guest shopper is offered an account, pre-filled from the order, which they can decline

## Issues with no doc section

- CHK-210 Klarna for guest orders (Backlog, Story)

## Issues pointing at a section the doc doesn't have

- CHK-211 3-D Secure exemption handling for guest payments: points at R8

## Issues for a Won't-have requirement

- CHK-209 Save card for guest shoppers: R7 is Won't have in the doc

## Coverage

| Section | MoSCoW | Issues |
|---|---|---|
| G1 | - | CHK-201 (In Progress) |
| G2 | - | CHK-202 (To Do) |
| R1 | M | CHK-203 (In Progress) |
| R2 | M | CHK-204 (To Do) |
| R3 | S | - |
| R4 | M | CHK-206 (To Do) |
| R5 | M | CHK-207 (To Do) |
| R6 | S | CHK-208 (To Do) |
| R7 | W | CHK-209 (To Do) |

Linked by mentioning the ID rather than a Source line (check these): CHK-207

```

**What the user gets back,** after reading the four flagged issues:

| Drift | Item | What happened | Fix |
|---|---|---|---|
| Doc section with no issue | R3 (Should) | CHK-205 was cancelled: "growth team will run this as an experiment later" | Either move R3 to Won't have in the PRD, or reopen CHK-205. The doc and the tracker currently disagree |
| Issue for a Won't-have requirement | CHK-209 Save card for guest shoppers | Added because "Sales asked for this"; the PRD rules it out | Close CHK-209, or change R7 in the PRD first. Scope changes go through the doc |
| Issue pointing at a missing section | CHK-211 3-D Secure exemption (In Progress) | Points at R8, which the PRD doesn't have. Its description answers the PRD's open question | Add the answer and a requirement to the PRD, then relink CHK-211 |
| Issue with no doc section | CHK-210 Klarna for guest orders | Not in the PRD | Ask whether Klarna-on-guest is in scope. If yes, add a requirement; if not, move it out of the epic |
| Linked by mention | CHK-207 | Its Source line was deleted; it mentions R5 | Restore the line: `Source: …#requirements (R5)` |

R1, R2, R4, R5 and R6 each have exactly one live issue.
