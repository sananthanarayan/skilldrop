# Open PRs touching billing-service (as of 2026-10-19)

| PR   | Title                                   | Author  | Files                                              | State                         |
|------|-----------------------------------------|---------|----------------------------------------------------|-------------------------------|
| #412 | Cap late fees at 10% of net for EU      | priya.n | InvoiceService.kt (applyLateFees), InvoiceServiceTest.kt | Approved, waiting on finance sign-off, expected to merge this week |
| #415 | Credit notes                            | tomasz  | InvoiceService.kt (new issueCreditNote, changes void), CreditNote.kt, V44__credit_notes.sql | Draft, ~3 weeks out |
| #409 | Bump Spring Boot 3.3.4 -> 3.3.5         | bot     | build.gradle.kts                                   | Green, ready                  |

Feature work continues on billing-service through Q4; no freeze is planned.
