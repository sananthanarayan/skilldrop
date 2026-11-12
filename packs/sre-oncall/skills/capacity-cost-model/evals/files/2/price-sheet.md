# Nimbus Cloud price sheet (excerpt, USD, region: north-1)

| Item | Price | Notes |
|---|---|---|
| Ingestion queue | $0.40 per million messages | |
| Ingestion worker (2 vCPU) | $70 per worker per month | Each worker processes up to 500 readings per second. Autoscaling adds workers with about a 3-minute delay. |
| Time-series DB, Standard tier | $400 per month flat | Up to 5,000 writes per second sustained. One reading = one write. |
| Time-series DB, Enterprise tier | $2,400 per month flat | Up to 50,000 writes per second sustained. |
| Time-series DB storage (either tier) | $0.12 per GB-month | A stored reading takes about 64 bytes after compression. |
| Archive storage | $0.01 per GB-month | Retrieval takes up to 12 hours. |
| Log ingestion | $0.50 per GB | Ingestion workers log one line of about 300 bytes per reading at the default level. |
| Data transfer out (to internet or on-premises) | $0.09 per GB | |
| NAT gateway | $32 per gateway per month + $0.045 per GB processed | |
