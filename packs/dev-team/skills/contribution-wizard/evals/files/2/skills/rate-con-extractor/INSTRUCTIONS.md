# rate-con-extractor

## Purpose

A rate confirmation is the agreement between Larkfield and a carrier for one load. Billing needs its numbers in a fixed shape before anything can be checked against it. This skill reads one rate confirmation and returns those numbers as a table.

## Steps

1. Find the load number, the carrier name, the pickup and delivery dates.
2. Find the linehaul rate. Record whether it is a flat amount or a per-mile rate, and the miles if per-mile.
3. Find the fuel surcharge. Record it as written: a percentage of linehaul, a per-mile amount, or a flat amount.
4. List every accessorial the document names (detention, lumper, layover, stop-off, tarp) with its rate and any free time or cap.
5. Return one table: field, value, and the line of the document the value came from.
6. List any field in steps 1 to 4 that the document does not state, under "Not stated".

## Never

- Never calculate a total. This skill extracts; it does not add up.
- Never fill a missing field from what is usual for the lane or the carrier.
- Never merge two rate confirmations into one table.
