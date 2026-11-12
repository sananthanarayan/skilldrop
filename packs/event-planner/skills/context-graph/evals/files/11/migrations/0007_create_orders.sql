CREATE TABLE orders (
    id             BIGINT PRIMARY KEY,
    customer_id    BIGINT NOT NULL,
    status         VARCHAR(16) NOT NULL DEFAULT 'draft',
    currency       CHAR(3) NOT NULL,
    subtotal_minor INTEGER NOT NULL,
    shipping_minor INTEGER NOT NULL DEFAULT 0,
    total_minor    INTEGER NOT NULL,
    placed_at      TIMESTAMPTZ
);
CREATE INDEX orders_customer_id_idx ON orders (customer_id);
