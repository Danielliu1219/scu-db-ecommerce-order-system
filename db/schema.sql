CREATE DATABASE IF NOT EXISTS scu_ecommerce
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE scu_ecommerce;
SET NAMES utf8mb4 COLLATE utf8mb4_0900_ai_ci;
SET SESSION time_zone = '+08:00';
SET SESSION transaction_isolation = 'READ-COMMITTED';
SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE TABLE users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(32) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(10) COLLATE utf8mb4_bin NOT NULL DEFAULT 'USER',
  nickname VARCHAR(50) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_username (username),
  KEY idx_users_role_created (role, created_at, id),
  CONSTRAINT ck_users_username CHECK (CHAR_LENGTH(TRIM(username)) BETWEEN 3 AND 32),
  CONSTRAINT ck_users_password CHECK (CHAR_LENGTH(TRIM(password_hash)) > 0),
  CONSTRAINT ck_users_role CHECK (role IN ('USER', 'ADMIN')),
  CONSTRAINT ck_users_nickname CHECK (CHAR_LENGTH(TRIM(nickname)) > 0),
  CONSTRAINT ck_users_phone CHECK (CHAR_LENGTH(TRIM(phone)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE category (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_category_name (name),
  CONSTRAINT ck_category_name CHECK (CHAR_LENGTH(TRIM(name)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE product (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  description TEXT NOT NULL,
  status VARCHAR(10) COLLATE utf8mb4_bin NOT NULL DEFAULT 'OFF_SHELF',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_product_category_status_price (category_id, status, price, id),
  KEY idx_product_status_price (status, price, id),
  CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES category (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_product_name CHECK (CHAR_LENGTH(TRIM(name)) > 0),
  CONSTRAINT ck_product_price CHECK (price > 0),
  CONSTRAINT ck_product_status CHECK (status IN ('ON_SHELF', 'OFF_SHELF'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE cart (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_cart_user (user_id),
  CONSTRAINT fk_cart_user FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE cart_item (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  cart_id BIGINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  selected TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_cart_item_product (cart_id, product_id),
  KEY idx_cart_item_product (product_id),
  CONSTRAINT fk_cart_item_cart FOREIGN KEY (cart_id) REFERENCES cart (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_cart_item_product FOREIGN KEY (product_id) REFERENCES product (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_cart_item_quantity CHECK (quantity > 0),
  CONSTRAINT ck_cart_item_selected CHECK (selected IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE orders (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  checkout_token CHAR(32) COLLATE utf8mb4_bin NOT NULL,
  checkout_request_hash CHAR(64) COLLATE utf8mb4_bin NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  status VARCHAR(12) COLLATE utf8mb4_bin NOT NULL DEFAULT 'PENDING',
  receiver_name VARCHAR(50) NOT NULL,
  receiver_phone VARCHAR(20) NOT NULL,
  receiver_address VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  paid_at DATETIME NULL DEFAULT NULL,
  shipped_at DATETIME NULL DEFAULT NULL,
  completed_at DATETIME NULL DEFAULT NULL,
  cancelled_at DATETIME NULL DEFAULT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_orders_user_token (user_id, checkout_token),
  KEY idx_orders_user_created (user_id, created_at, id),
  KEY idx_orders_status_created (status, created_at, id),
  KEY idx_orders_created (created_at, id),
  CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_orders_token CHECK (CHAR_LENGTH(checkout_token) = 32),
  CONSTRAINT ck_orders_hash CHECK (CHAR_LENGTH(checkout_request_hash) = 64),
  CONSTRAINT ck_orders_total CHECK (total_amount > 0),
  CONSTRAINT ck_orders_receiver CHECK (
    CHAR_LENGTH(TRIM(receiver_name)) > 0 AND
    CHAR_LENGTH(TRIM(receiver_phone)) > 0 AND
    CHAR_LENGTH(TRIM(receiver_address)) > 0
  ),
  CONSTRAINT ck_orders_status_times CHECK (
    (status = 'PENDING' AND paid_at IS NULL AND shipped_at IS NULL
      AND completed_at IS NULL AND cancelled_at IS NULL)
    OR (status = 'PAID' AND paid_at IS NOT NULL AND shipped_at IS NULL
      AND completed_at IS NULL AND cancelled_at IS NULL)
    OR (status = 'SHIPPED' AND paid_at IS NOT NULL AND shipped_at IS NOT NULL
      AND completed_at IS NULL AND cancelled_at IS NULL)
    OR (status = 'COMPLETED' AND paid_at IS NOT NULL AND shipped_at IS NOT NULL
      AND completed_at IS NOT NULL AND cancelled_at IS NULL)
    OR (status = 'CANCELLED' AND paid_at IS NULL AND shipped_at IS NULL
      AND completed_at IS NULL AND cancelled_at IS NOT NULL)
  ),
  CONSTRAINT ck_orders_time_sequence CHECK (
    (paid_at IS NULL OR paid_at >= created_at) AND
    (shipped_at IS NULL OR shipped_at >= paid_at) AND
    (completed_at IS NULL OR completed_at >= shipped_at) AND
    (cancelled_at IS NULL OR cancelled_at >= created_at)
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE order_item (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id BIGINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  product_name VARCHAR(100) NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  quantity INT NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_order_item_product (order_id, product_id),
  KEY idx_order_item_product_order (product_id, order_id),
  CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES orders (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_order_item_product FOREIGN KEY (product_id) REFERENCES product (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_order_item_name CHECK (CHAR_LENGTH(TRIM(product_name)) > 0),
  CONSTRAINT ck_order_item_price CHECK (unit_price > 0),
  CONSTRAINT ck_order_item_quantity CHECK (quantity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE inventory (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  product_id BIGINT UNSIGNED NOT NULL,
  available INT NOT NULL DEFAULT 0,
  version BIGINT UNSIGNED NOT NULL DEFAULT 0,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_inventory_product (product_id),
  CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) REFERENCES product (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_inventory_available CHECK (available >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE payment (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id BIGINT UNSIGNED NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  paid_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_payment_order (order_id),
  KEY idx_payment_paid_order (paid_at, order_id),
  CONSTRAINT fk_payment_order FOREIGN KEY (order_id) REFERENCES orders (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_payment_amount CHECK (amount > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
