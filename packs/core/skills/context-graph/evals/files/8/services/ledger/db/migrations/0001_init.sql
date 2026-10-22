CREATE TABLE accounts (
    id            UUID PRIMARY KEY,
    currency      CHAR(3) NOT NULL,
    balance_minor BIGINT  NOT NULL DEFAULT 0,
    frozen        BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE entries (
    id           UUID PRIMARY KEY,
    account_id   UUID    NOT NULL REFERENCES accounts(id),
    amount_minor BIGINT  NOT NULL,
    currency     CHAR(3) NOT NULL,
    posted_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
