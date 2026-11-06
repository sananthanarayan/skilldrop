---
title: Atlas WMS migration — week 42 status
author: Priya Nair, Programme Lead
date: 22 October 2026
---

# Atlas WMS migration: week 42 status

## Summary

- Overall status: **Amber** (Green in week 40)
- Leeds go-live moves from 9 Nov to 23 Nov
- Budget: £412k spent of £640k (64%)
- Two of five integration streams complete

<!-- notes: Open with the date change; the steering group will ask about it first. -->

## Milestones

| Milestone | Owner | Planned | Forecast | Status |
|---|---|---|---|---|
| Data migration dry run 1 | Tomasz | 15 Sep | 15 Sep | Done |
| Carrier API integration | Lena | 1 Oct | 8 Oct | Done |
| Data migration dry run 2 | Tomasz | 20 Oct | 27 Oct | Late |
| User acceptance testing | Aisha | 27 Oct | 10 Nov | At risk |
| Leeds go-live | Priya | 9 Nov | 23 Nov | At risk |

## Defect burn-down

![Open defects by week, weeks 36 to 42](img/defect-burndown.png)

Open defects fell from 148 to 61 over seven weeks. 9 of the 61 are severity 1.

## Risks and issues

### Risks

- **Dry run 2 slips again.** The source extract from the legacy system still times out on the
  pallet history table, which holds eleven years of movements.
  - Mitigation: archive movements older than three years before the extract
  - Owner: Tomasz, decision needed by 24 Oct
- **UAT testers not released.** Leeds shift managers are needed for five days and peak season
  starts on 16 Nov.
  - Mitigation: split UAT into two blocks of two and a half days
  - Owner: Aisha
- **Carrier label format change.** One carrier changes its label layout on 1 Nov, which the
  integration built in October does not support yet.
  - Mitigation: Lena has the new specification; estimate is three days of work
- **Handheld scanner firmware.** 40 of the 120 handhelds at Leeds run firmware older than the
  minimum the new WMS supports.
  - Mitigation: firmware update in the week of 2 Nov, outside picking hours

### Issues

- **Severity 1 defects.** 9 open, 6 of them in replenishment rules; fixes are due in the
  build of 29 Oct.
- **Training rooms.** The Leeds training room is booked for audits in the week of 9 Nov, so
  training moves to the Wakefield site.
- **Test data.** UAT needs a masked copy of production data, and the masking job has not been
  approved by the data protection officer yet.

<!-- notes: Don't raise the Pellow Freight penalty clause (£35k if go-live slips past 30 Nov) unless they ask; legal is still reviewing it. -->

## Decisions needed

1. Approve archiving pallet movements older than three years before dry run 2
2. Approve the new Leeds go-live date of 23 Nov
3. Release four Leeds shift managers for UAT in two blocks

## Next two weeks

- Dry run 2 on 27 Oct, with the archive in place
- Replenishment fixes in the 29 Oct build
- Scanner firmware update in the week of 2 Nov
- Full plan and RAID log: [programme site](https://atlas.harbourline.example/programme)
