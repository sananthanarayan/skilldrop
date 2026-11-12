-- 2022-09-30: per-customer custom fields as JSONB instead of new columns
ALTER TABLE shipments ADD COLUMN custom_fields JSONB NOT NULL DEFAULT '{}'::jsonb;
CREATE INDEX shipments_custom_fields_gin ON shipments USING GIN (custom_fields);
