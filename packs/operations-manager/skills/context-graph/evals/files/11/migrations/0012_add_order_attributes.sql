-- DR-014: optional customer-supplied order fields.
ALTER TABLE orders ADD COLUMN attributes JSONB NOT NULL DEFAULT '{}'::jsonb;
