# Tables (Snowflake, database TARNVALLEY)

## FIELD.JOBS — one row per visit
| column | type | notes |
|---|---|---|
| job_id | NUMBER | primary key |
| address_id | NUMBER | always filled |
| appliance_id | NUMBER | NULL for every job before 2026-03-03 |
| job_type | VARCHAR | 'repair', 'recall', 'annual_service', 'install' |
| status | VARCHAR | 'completed', 'cancelled', 'no_access' |
| follow_up_required | BOOLEAN | ticked by the engineer on closing the job |
| engineer_id | NUMBER | |
| created_at | TIMESTAMP_NTZ | UK local time, when the job was booked |
| completed_at | TIMESTAMP_NTZ | UK local time, NULL unless status = 'completed' |

There is no column that links a recall, or any later visit, to the job it follows.

## FIELD.APPLIANCES
| column | type | notes |
|---|---|---|
| appliance_id | NUMBER | primary key |
| address_id | NUMBER | |
| make | VARCHAR | |
| model | VARCHAR | |
| installed_on | DATE | often NULL |

## FIELD.ENGINEERS
| column | type | notes |
|---|---|---|
| engineer_id | NUMBER | primary key |
| region | VARCHAR | 'north', 'central', 'coast' |
| employment_type | VARCHAR | 'employed', 'subcontractor' |
