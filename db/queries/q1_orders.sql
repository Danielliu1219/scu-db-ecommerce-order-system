SELECT o.id AS order_id, o.user_id, u.username,
       o.status, o.created_at, o.total_amount,
       o.receiver_name, o.receiver_phone, o.receiver_address,
       o.paid_at, o.shipped_at, o.completed_at, o.cancelled_at,
       oi.id AS order_item_id, oi.product_id, oi.product_name,
       oi.unit_price, oi.quantity, oi.unit_price * oi.quantity AS line_amount,
       p.id AS payment_id, p.amount AS payment_amount, p.paid_at AS payment_time
FROM orders AS o
JOIN users AS u ON u.id = o.user_id
JOIN order_item AS oi ON oi.order_id = o.id
LEFT JOIN payment AS p ON p.order_id = o.id
WHERE (CAST(:user_id AS NUMERIC(20,0)) IS NULL OR o.user_id = CAST(:user_id AS NUMERIC(20,0)))
  AND (CAST(:status AS VARCHAR(12)) IS NULL OR o.status = CAST(:status AS VARCHAR(12)))
  AND o.created_at >= :start_at AND o.created_at < :end_at
ORDER BY o.created_at DESC, o.id DESC, oi.id ASC;
