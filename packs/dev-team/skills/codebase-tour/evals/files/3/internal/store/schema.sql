CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY,
  endpoint_url TEXT NOT NULL,
  payload BYTEA NOT NULL,
  state TEXT NOT NULL DEFAULT 'pending'
);
