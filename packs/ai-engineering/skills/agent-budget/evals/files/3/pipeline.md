# Claims-intake agent pipeline (Pellmore Mutual)

One "run" = one pass of the pipeline for one claim.

| # | Stage | Model | What it does |
|---|-------|-------|--------------|
| 1 | extract | Core | Reads the claim documents (forms, photos, PDFs) and outputs structured fields |
| 2 | classify | Core | Assigns claim type and urgency |
| 3 | fraud_check | Apex | Scores fraud signals and writes a short rationale for the adjuster |
| 4 | draft_letter | Apex | Drafts the acknowledgement letter to the customer |
| 5 | adjuster review | (human) | An adjuster approves or edits the letter and the routing before anything goes out |

Retry behaviour: if any stage's output fails schema validation, the whole run restarts from
stage 1. There is currently no limit on restarts.

Compliance commitment: in our 2026 audit response to the regulator (ref MR-2026-14) we committed
that the fraud screening model and its configuration will not change without 90 days' notice and
re-validation by Model Risk. The next review window opens in February 2027.
