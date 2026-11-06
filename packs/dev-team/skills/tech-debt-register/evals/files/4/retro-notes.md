# Warehouse Systems, Q3 retro: debt column (raw, as written on the board)

Team: Kestrel Freight warehouse systems, Hollins depot. Five engineers.

- (Marta) The nightly stock sync between the WMS and the finance ledger drops rows when a pallet is
  split. Finance reconciles by hand every Monday. Oleksandr in finance says it takes him about half
  a day each week.
- (Ines) Monday reconciliation is painful because the sync misses split pallets. Can we fix the
  sync?
- (Tomas) Sync failures cost us about 40 engineer-hours this quarter.
- (Marta) Doing the stock sync properly (rewrite on the new event feed) is a big job: two people
  for a full quarter. A targeted patch for split pallets only is about 3 days.
- (Dev) The old Perl reporting scripts are horrible. Nobody wants to touch them. We should rewrite
  them in Python.
- (Tomas) The label printing service crashes every week and we restart it by hand.
- (Marta) The handheld scanners talk to the WMS API through a TLS certificate that Raj used to renew
  by hand. Raj left in August and nobody knows where his renewal notes are. The gateway shows the
  certificate expires on 2026-12-01. If it lapses, every scanner on the floor stops.
- (Dev) The WMS adapter test suite takes 50 minutes, so people skip it before deploys.
- (Ines) Both putaway incidents this quarter came from deploys where the tests were skipped.
- (Ines) Speeding the adapter tests up to under 10 minutes: Dev thinks about a week of work.
