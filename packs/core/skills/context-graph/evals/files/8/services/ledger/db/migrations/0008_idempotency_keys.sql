CREATE TABLE idempotency_keys (
    key          TEXT PRIMARY KEY,
    response     JSONB NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
