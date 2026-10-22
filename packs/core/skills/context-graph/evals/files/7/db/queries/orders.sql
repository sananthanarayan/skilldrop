-- name: get_order
SELECT id, tenant_id, total_minor FROM orders WHERE id = %(id)s AND tenant_id = %(tenant_id)s;
