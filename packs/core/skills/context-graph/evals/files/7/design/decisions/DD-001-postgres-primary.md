# DD-001: Postgres is the primary datastore

Status: Accepted
Date: 2022-04-11
Deciders: O. Mensah
Governs: db/, services/

All service state lives in Postgres. No second OLTP database without a new decision.
