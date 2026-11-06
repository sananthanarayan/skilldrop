# Worked example: a supplier's SaaS agreement

## Input

> *"Northgate sent their SaaS agreement for the analytics platform, it's in
> [inputs/saas-agreement.md](inputs/saas-agreement.md). We're Brightloop, the customer. The
> first year would end on 1 July 2027. Anything I should push back on before I sign?"*

## What the check found

```text
27 numbered clauses, 8 defined terms, 2 schedules or exhibits (Exhibit A, Exhibit B).

FAIL [line 3] “31 June 2026” is not a real date
FAIL [line 17, clause 2.1] refers to Exhibit C, which isn't in the document
FAIL [line 23, clause 3.1] a [●] placeholder is still in: “…all pay the Fees of [●] per month, invoiced monthly in advan…”
FAIL [line 25, clause 3.2] “thirty (60)”: the words say 30 and the figure says 60
FAIL [line 39, clause 5.2] “Confidential Information” is defined more than once (lines 9, 39)
FAIL [line 53, clause 8.2] refers to section 14.3, which doesn't exist
FAIL [line 59, clause 9.1] a blank line to fill in is still in: “Signed: ____________________”
WARN [line 9, clause 1.2] “Confidential Information” is defined but never used
WARN [line 11, clause 1.3] “Customer Data” is defined but never used
WARN [line 17, clause 2.1] “Effective Date” is used as a defined term (capitalised, 2 times) but never defined
WARN [line 31, clause 4.1] “Initial Term” is defined but never used
WARN [line 37, clause 5.1] “confidential information” appears in lower case although “Confidential Information” is a defined term (lines 37)
WARN [line 47, clause 6.3] “Client” is used as a defined term (capitalised, 2 times) but never defined
WARN [line 49, clause 8] clause numbering jumps to 8; 7 is missing

Notice periods:
- 60 days (line 33, clause 4.2) — give notice by 2027-05-02: …ives at least sixty (60) days' written notice before the end of the then-current term.
- 90 days (line 51, clause 8.1): …Agreement on ninety (90) days' written notice.
```

## Reply

**Don't sign it yet. Three things:** the monthly fee is still a blank (3.1); the agreement
promises service levels in Exhibit C, but there is no Exhibit C (2.1); and you would
indemnify Northgate for any claim arising from your use of the platform, with no cap (6.3),
while their liability to you is capped at three months' fees (6.1).

**Fixes before signing**

- 🟥 **6.3, indemnity.** As written, if a third party sues Northgate over anything you did on
  the platform, you pay all of it. Ask for: *"Each party shall indemnify the other against
  third-party claims arising from its own breach of this Agreement or its negligence, subject
  to clause 6.1."*
- 🟥 **6.1, liability cap.** It caps only Northgate's liability, at three months' fees. Ask for:
  *"Each party's total liability is limited to the fees paid or payable in the 12 months
  before the claim."*
- 🟧 **3.3, late payment.** 4 % a month is 48 % a year. Ask for interest at 2 % above the base
  rate, a year.
- 🟧 **2.2, changes.** They can change the platform at any time. Ask for 30 days' notice of any
  change that removes a feature you use, with a right to terminate if it does.
- 🟨 **4.2, renewal.** It renews for another year unless you give 60 days' notice. Ask for 30.

**Mechanical faults to correct**

- 3.1: the fee is `[●]`. It should be $2,000 a month, as Exhibit B says.
- 3.2: "thirty (60) days". Ask which they meant.
- 2.1: refers to Exhibit C, which isn't attached. Ask for it before signing: it holds the
  service levels.
- 8.2: says Section 14.3 survives termination, but the agreement ends at clause 9.
- 5.2: defines "Confidential Information" a second time; 5.1 uses it in lower case.
- 6.3: says "the Client" where the agreement defines "the Customer".
- The agreement is dated 31 June 2026, which doesn't exist; clause 7 is missing; "Effective
  Date" is used but never defined.

**Dates to diarise**

- Notice not to renew: by **2 May 2027** (60 days before 1 July 2027).

**Worth a lawyer's hour:** only if Northgate refuses to cap or narrow the indemnity in 6.3.
