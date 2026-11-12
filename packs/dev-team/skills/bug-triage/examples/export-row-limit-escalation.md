# Worked example: an escalated "exports are losing data" report

Input → output oracle for `bug-triage`. Shows severity judged from the evidence rather than
the escalation, a paraphrased error replaced by the verbatim string, and a three-symptom
thread split into one bug, one more bug and one feature request.

## Input

> Can you turn this into a ticket for the Reports squad? Our VP of Customer Success wants it
> filed as S1/P1 today. Tallow & Finch renew next month and they're furious.
>
> **#cs-escalations (pasted):**
>
> **Dana (CSM), 09:12:** Tallow & Finch say exports are losing data. Their ops lead exported
> the Shipment Activity report for October and "half the shipments are gone". Got some random
> error when it finished. Started after last week's release I think.
>
> **Dana, 09:14:** Also their dates come out as MM/DD in the CSV even though their account is
> set to DD/MM. And they asked again for scheduled exports to SFTP.
>
> **Dana, 09:20:** Screenshot text from their ops lead: "Export ready. Some rows may not be
> included. (EXPORT_ROW_LIMIT_REACHED)"
>
> **Marco (support engineer), 09:41:** Pulled the job log:
>
> ```
> 2026-11-04T08:57:31Z export_job id=exp_88213 tenant=tallow-finch.example
>   report=shipment_activity range=2026-10-01..2026-10-31 format=csv status=completed
>   rows_matched=14212 rows_written=10000 warning=EXPORT_ROW_LIMIT_REACHED app=5.18.2
> ```
>
> **Marco, 09:43:** The shipments are all there in the app, btw. The report shows 14,212 rows
> on screen.

## Output

Filed as **S3/P2, not S1/P1.** Nothing stored was lost: the app still shows all 14,212 rows.
The export file stops at 10,000. That is a real bug with a likely workaround. The VP can raise
the priority to P1 for the renewal, but that changes priority only. The severity stays S3.
The thread also held two other items, split out at the bottom.

```markdown
# CSV export of Shipment Activity stops at 10,000 rows (EXPORT_ROW_LIMIT_REACHED); remaining rows missing from file

**Severity:** S3 — the export file is incomplete, stored data is intact, and splitting the date range likely works around it
**Priority:** P2 — one tenant confirmed, renewal next month; a workaround CS can hand over today removes the need to drop current work
**Blast radius:** any export over 10,000 rows, on any tenant `[assumption]`; one tenant confirmed `[verified]`
**Component (best guess):** report export job `[assumption]`

## Summary

A customer ops lead exported October's Shipment Activity report as CSV. The file holds 10,000
of the 14,212 matching rows `[verified: job log exp_88213]`. The dialog warned that rows "may
not be included" `[reported: screenshot text]`. All 14,212 rows still show in the app
`[verified: Marco, on screen]`.

## Environment

| Field | Value | Tag |
|---|---|---|
| App version | 5.18.2 | `[verified]` |
| Tenant | tallow-finch.example | `[verified]` |
| Report / range / format | shipment_activity, 2026-10-01..2026-10-31, CSV | `[verified]` |
| Time | 2026-11-04 08:57:31 UTC | `[verified]` |
| First seen / last worked | "after last week's release" | `[reported]` |

## Reproduction

**No repro yet.** One occurrence is confirmed in the log and nobody has reproduced it. Collect:
- An export of any report with more than 10,000 matching rows on a test tenant, run on 5.18.2.
  Record rows_matched and rows_written from the job log.
- The downloaded file from exp_88213, to count its rows and check whether it ends cleanly at
  row 10,000 or mid-row
- Export job logs from the 30 days before last week's release, filtered on
  `rows_written=10000`
- A screenshot of the full export dialog, to check whether it states the limit or only "may
  not be included"

## Expected vs actual

**Expected:** the CSV contains all 14,212 rows the report shows, or the export refuses and names the limit
**Actual:** the CSV contains 10,000 rows, the job status is `completed`, and the dialog shows a vague warning
**Error (verbatim):** `Export ready. Some rows may not be included. (EXPORT_ROW_LIMIT_REACHED)`

## Hypotheses (≤3 — each with a 5-minute check; none of these is a conclusion)

| # | Hypothesis | Quick check |
|---|---|---|
| H1 | 10,000 is a deliberate cap that was never documented | Search the export service config and docs for `10000` or `EXPORT_ROW_LIMIT` |
| H2 | The cap or its warning arrived in a recent release | Filter export logs before last week's release for `rows_written=10000` |
| H3 | Pagination stops after a fixed number of pages rather than a fixed row count | Export 10,001 rows and then 25,000 rows on a test tenant and compare rows_written |

## Questions for reporter (≤3, ranked by diagnostic value)

1. Has the ops lead had a complete export of more than 10,000 rows before? When was the last one?
2. Do two half-month exports (Oct 1–15 and Oct 16–31) each come out complete?
3. What does the file feed: a person reading it, or another system that will treat it as complete?

## Duplicate-search hints

`EXPORT_ROW_LIMIT_REACHED` · `export missing rows` · `csv export 10000`

## Split out (if the report contained more than one issue)

- CSV export writes dates as MM/DD when the account date format is DD/MM → to be filed as its own bug
- Scheduled exports to SFTP → feature request, not a bug; route to the product backlog
```

## Why this is the oracle

- **Severity is judged on worst plausible impact, and priority is judged separately.** The
  reporter's words ("losing data", "half gone") and the VP's pressure both point at S1. The
  evidence shows an incomplete file over intact data with a likely workaround, so the ticket
  says S3. The VP's urgency is a legitimate input to priority, so the reply leaves that lever
  with the VP and does not let it move severity.
- **Tags separate reported from verified.** "Half the shipments are gone" is `[reported]`. The
  log shows 10,000 of 14,212, about 70%, written. "After last week's release" stays a
  hypothesis with a check (H2), not a stated cause.
- **The verbatim error replaces the paraphrase, and one bug gets one ticket.** The "random
  error" is quoted as the exact string, which is also the best duplicate-search term. The date
  bug and the SFTP request get split out.

A cheaper pass titles it "Exports losing data", files S1/P1 as asked, writes "Cause: 10k row
limit introduced in 5.18" as fact, invents repro steps nobody ran, and puts the date bug in
the same ticket. That ticket gets fixed in a rush on a guessed cause, and the date bug goes
nowhere.
