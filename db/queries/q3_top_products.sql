SELECT oi.product_id, pr.name AS product_name,
       SUM(oi.quantity) AS sold_quantity
FROM payment AS p
JOIN orders AS o ON o.id = p.order_id
JOIN order_item AS oi ON oi.order_id = o.id
JOIN product AS pr ON pr.id = oi.product_id
WHERE p.paid_at >= :start_at AND p.paid_at < :end_at
  AND o.status IN ('PAID', 'SHIPPED', 'COMPLETED')
GROUP BY oi.product_id, pr.name
ORDER BY sold_quantity DESC, oi.product_id ASC
LIMIT 10;
