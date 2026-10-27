-- FX conversions: store the converted amount and the rate used.
ALTER TABLE entries ADD COLUMN fx_amount   NUMERIC(18,4);
ALTER TABLE entries ADD COLUMN fx_currency CHAR(3);
ALTER TABLE entries ADD COLUMN fx_rate     NUMERIC(18,8);
