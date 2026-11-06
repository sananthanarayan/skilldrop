# shelfline

Holds and catalogue service for the Example County Library branches.

## Components

- **API** (`app/api.py`) - small Flask app: catalogue search, placing holds, checking books back in.
- **Postgres** - patrons, copies, loans, holds, fines.
- **Redis** - caches search results and keeps each patron's place in the hold queue.
- **Notifier** (`app/notify.py`) - tells patrons when a held book is ready to collect.
- **Fines job** (`jobs/fines.py`) - nightly, works out overdue fines.

## Running locally

    export DATABASE_URL=postgres://localhost/shelfline
    export NOTIFY_WEBHOOK_URL=http://localhost:9000/hooks/ready
    flask --app app.api run
