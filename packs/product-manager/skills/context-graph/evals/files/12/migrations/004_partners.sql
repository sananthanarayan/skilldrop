CREATE TABLE partners (
    id         text PRIMARY KEY,
    url        text NOT NULL,
    events     text[] NOT NULL,
    secret_ref text NOT NULL,
    enabled    boolean NOT NULL DEFAULT true
);
