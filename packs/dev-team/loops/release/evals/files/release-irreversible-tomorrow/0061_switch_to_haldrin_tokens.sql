-- Migration 0061: switch payment_methods to Haldrin Pay tokens
-- PR #845. Runs inside the 5 Nov deploy, before the new app pods start.

BEGIN;

ALTER TABLE payment_methods ADD COLUMN provider_token text;

UPDATE payment_methods pm
SET provider_token = m.provider_token
FROM card_token_map m
WHERE m.legacy_card_token = pm.legacy_card_token;

-- Cards with no Haldrin match are marked so the app asks the customer to re-enter them.
UPDATE payment_methods
SET status = 'needs_reentry'
WHERE provider_token IS NULL;

ALTER TABLE payment_methods DROP COLUMN legacy_card_token;

DROP TABLE card_token_map;

COMMIT;
