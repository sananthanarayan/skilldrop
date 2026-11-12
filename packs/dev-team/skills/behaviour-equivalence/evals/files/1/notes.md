# Quote service rewrite: parity run

Owner: Priya Raman (checkout team). Cutover planned for the release train after next.

- `cases.jsonl`: the 12 requests we replayed. Taken from the staging request log on 12 Oct and
  topped up with the error cases by hand. Promo codes aren't in this set: staging doesn't have
  the promo service, so no request carries one.
- `old.jsonl`, `old_rerun.jsonl`: `pricing_v1.quote` run twice on those requests (09:14 and
  09:41 on 12 Oct).
- `new.jsonl`: `pricing_v2.quote` on the same requests (14 Oct).
- `rules.json`: our normalisation rules. With them the diff tool says every case matches.

Differences we saw before normalising: timestamps, quote IDs, line order, and a few 1p
rounding differences between the Decimal code paths, which the tolerance rules cover. We'd
like to call this equivalent and book the cutover.
