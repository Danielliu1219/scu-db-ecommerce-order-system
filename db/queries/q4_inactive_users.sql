SELECT u.id AS user_id, u.username, u.nickname, u.phone, u.created_at
FROM users AS u
WHERE u.role = 'USER'
  AND u.created_at <= :as_of
  AND NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
      AND o.created_at >= :as_of - INTERVAL 30 DAY
      AND o.created_at < :as_of
  )
ORDER BY u.id ASC;
