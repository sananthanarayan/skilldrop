-- name: PendingEvents :many
SELECT id, endpoint_url, payload FROM events WHERE state = 'pending' ORDER BY id LIMIT $1;

-- name: DeadEvents :many
SELECT id, endpoint_url, payload FROM events WHERE state = 'dead' ORDER BY id;

-- name: MarkDelivered :exec
UPDATE events SET state = 'delivered' WHERE id = $1;

-- name: MarkDead :exec
UPDATE events SET state = 'dead' WHERE id = $1;
