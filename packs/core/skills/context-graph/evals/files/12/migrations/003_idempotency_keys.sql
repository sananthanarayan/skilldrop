CREATE TABLE idempotency_keys (
    event_id   text        NOT NULL,
    partner_id text        NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (event_id, partner_id)
);
