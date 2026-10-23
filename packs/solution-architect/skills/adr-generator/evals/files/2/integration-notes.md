# Lab results integration — working group notes, 9 Oct 2026

Attendees: integration lead, chief clinical information officer (CCIO), lab IT manager, EPR product owner, finance business partner

## Problem
Lab results reach the electronic patient record (EPR) through a nightly file drop. Clinicians at all four sites (Ashby, Brenmoor, Calder Street, Dunmere) can see results up to 24 hours late. The deteriorating-patient audit (Aug 2026) found 3 cases where a critical potassium result was phoned through but not visible in the EPR for 9+ hours.

Clinical requirement (CCIO): critical results visible in the EPR within 15 minutes of lab sign-off; routine results within 2 hours.

## Options discussed
A. Keep the nightly batch and add an extra run every 4 hours. No licence cost. Does not meet the 15-minute requirement.
B. FHIR R4 subscriptions sent directly from the lab system to the EPR. The EPR supports this today. EPR product owner's preference.
C. Hosted integration engine (Larchway Connect) polling the lab system's export folder every 5 minutes and posting FHIR messages to the EPR.

## Points raised
- Lab IT manager: the lab system (Northmere Diagnostics, v8.2) can only do file export. FHIR subscriptions arrive in v9, which the vendor has scheduled for Q3 2027 "subject to change". There is no date commitment in the contract.
- Finance: £48k/yr is in the 2027 budget line for the integration engine, based on 3 sites at £16k per site.
- EPR product owner: "Let's just go with B and wait for v9 — it's the clean answer."
- CCIO: we cannot wait until Q3 2027 with the current 24-hour gap for critical results.
- The group leaned towards C now, moving to B once v9 is live. Not unanimous — the EPR product owner dissented.

## Next step
Integration lead to write this up as an ADR for the Architecture Review Board meeting on 24 Oct 2026. The ARB approves or rejects.
