SELECT DATE_FORMAT(p.paid_at, '%Y-%m') AS sales_month,
       SUM(o.total_amount) AS sales_amount,
       COUNT(*) AS paid_order_count
FROM payment AS p
JOIN orders AS o ON o.id = p.order_id
WHERE p.paid_at >= :start_at AND p.paid_at < :end_at
  AND o.status IN ('PAID', 'SHIPPED', 'COMPLETED')
GROUP BY DATE_FORMAT(p.paid_at, '%Y-%m')
ORDER BY sales_month ASC;
