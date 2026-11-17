SELECT u.id AS user_id, u.username, u.nickname, u.phone, u.created_at
FROM users AS u
WHERE u.role = 'USER'
  AND u.created_at <= CAST(:as_of AS TIMESTAMP)
  AND NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
      AND o.created_at >= CAST(:as_of AS TIMESTAMP) - INTERVAL '30 days'
      AND o.created_at < CAST(:as_of AS TIMESTAMP)
  )
ORDER BY u.id ASC;
