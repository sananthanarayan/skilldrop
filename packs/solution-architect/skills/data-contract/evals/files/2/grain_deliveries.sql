-- Harrowgate Grain Co-operative — warehouse.grain_deliveries
-- Loaded nightly (02:00) from the weighbridge export.
CREATE TABLE warehouse.grain_deliveries (
  delivery_id      VARCHAR(20)  NOT NULL PRIMARY KEY,  -- weighbridge ticket number
  delivered_at     TIMESTAMP    NOT NULL,              -- local time at the weighbridge
  site_code        CHAR(3)      NOT NULL,              -- HGT, MLB or RSW
  member_id        VARCHAR(10)  NOT NULL,              -- co-op member number
  farmer_name      VARCHAR(120),
  farmer_phone     VARCHAR(20),
  crop             VARCHAR(30)  NOT NULL,              -- wheat, barley, oilseed_rape, oats
  net_weight       NUMERIC(8,3) NOT NULL,              -- net weight in tonnes
  moisture_pct     NUMERIC(5,3),                       -- moisture content
  grade            CHAR(1),                            -- A, B, C or R (rejected); null until graded
  price_per_tonne  NUMERIC(8,2)                        -- GBP, set by the grading team; null until graded
);
