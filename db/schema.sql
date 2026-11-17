SET TIME ZONE 'Asia/Shanghai';
SET default_transaction_isolation = 'read committed';
CREATE COLLATION app_ci (provider = icu, locale = 'und-u-ks-level1', deterministic = false);

CREATE SEQUENCE users_id_seq AS BIGINT;
CREATE TABLE users (
  id NUMERIC(20,0) NOT NULL DEFAULT nextval('users_id_seq'),
  username VARCHAR(32) COLLATE app_ci NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(10) COLLATE "C" NOT NULL DEFAULT 'USER',
  nickname VARCHAR(50) COLLATE app_ci NOT NULL,
  phone VARCHAR(20) COLLATE app_ci NOT NULL,
  created_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai'),
  updated_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai'),
  PRIMARY KEY (id),
  CONSTRAINT uk_users_username UNIQUE (username),
  CONSTRAINT ck_users_username CHECK (CHAR_LENGTH(TRIM(username)) BETWEEN 3 AND 32),
  CONSTRAINT ck_users_password CHECK (CHAR_LENGTH(TRIM(password_hash)) > 0),
  CONSTRAINT ck_users_role CHECK (role IN ('USER', 'ADMIN')),
  CONSTRAINT ck_users_nickname CHECK (CHAR_LENGTH(TRIM(nickname)) > 0),
  CONSTRAINT ck_users_phone CHECK (CHAR_LENGTH(TRIM(phone)) > 0),
  CONSTRAINT ck_users_id_range CHECK (id BETWEEN 1 AND 18446744073709551615)
);
ALTER SEQUENCE users_id_seq OWNED BY users.id;

CREATE SEQUENCE category_id_seq AS BIGINT;
CREATE TABLE category (
  id NUMERIC(20,0) NOT NULL DEFAULT nextval('category_id_seq'),
  name VARCHAR(50) COLLATE app_ci NOT NULL,
  created_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai'),
  updated_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai'),
  PRIMARY KEY (id),
  CONSTRAINT uk_category_name UNIQUE (name),
  CONSTRAINT ck_category_name CHECK (CHAR_LENGTH(TRIM(name)) > 0),
  CONSTRAINT ck_category_id_range CHECK (id BETWEEN 1 AND 18446744073709551615)
);
ALTER SEQUENCE category_id_seq OWNED BY category.id;

CREATE SEQUENCE product_id_seq AS BIGINT;
CREATE TABLE product (
  id NUMERIC(20,0) NOT NULL DEFAULT nextval('product_id_seq'),
  category_id NUMERIC(20,0) NOT NULL,
  name VARCHAR(100) COLLATE app_ci NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  description TEXT COLLATE app_ci NOT NULL,
  status VARCHAR(10) COLLATE "C" NOT NULL DEFAULT 'OFF_SHELF',
  created_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai'),
  updated_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai'),
  PRIMARY KEY (id),
  CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES category (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_product_name CHECK (CHAR_LENGTH(TRIM(name)) > 0),
  CONSTRAINT ck_product_price CHECK (price > 0),
  CONSTRAINT ck_product_status CHECK (status IN ('ON_SHELF', 'OFF_SHELF')),
  CONSTRAINT ck_product_id_range CHECK (id BETWEEN 1 AND 18446744073709551615),
  CONSTRAINT ck_product_category_id_range CHECK (category_id BETWEEN 1 AND 18446744073709551615)
);
ALTER SEQUENCE product_id_seq OWNED BY product.id;

CREATE SEQUENCE cart_id_seq AS BIGINT;
CREATE TABLE cart (
  id NUMERIC(20,0) NOT NULL DEFAULT nextval('cart_id_seq'),
  user_id NUMERIC(20,0) NOT NULL,
  created_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai'),
  PRIMARY KEY (id),
  CONSTRAINT uk_cart_user UNIQUE (user_id),
  CONSTRAINT fk_cart_user FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_cart_id_range CHECK (id BETWEEN 1 AND 18446744073709551615),
  CONSTRAINT ck_cart_user_id_range CHECK (user_id BETWEEN 1 AND 18446744073709551615)
);
ALTER SEQUENCE cart_id_seq OWNED BY cart.id;

CREATE SEQUENCE cart_item_id_seq AS BIGINT;
CREATE TABLE cart_item (
  id NUMERIC(20,0) NOT NULL DEFAULT nextval('cart_item_id_seq'),
  cart_id NUMERIC(20,0) NOT NULL,
  product_id NUMERIC(20,0) NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  selected SMALLINT NOT NULL DEFAULT 1,
  created_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai'),
  updated_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai'),
  PRIMARY KEY (id),
  CONSTRAINT uk_cart_item_product UNIQUE (cart_id, product_id),
  CONSTRAINT fk_cart_item_cart FOREIGN KEY (cart_id) REFERENCES cart (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_cart_item_product FOREIGN KEY (product_id) REFERENCES product (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_cart_item_quantity CHECK (quantity > 0),
  CONSTRAINT ck_cart_item_selected CHECK (selected IN (0, 1)),
  CONSTRAINT ck_cart_item_id_range CHECK (id BETWEEN 1 AND 18446744073709551615),
  CONSTRAINT ck_cart_item_cart_id_range CHECK (cart_id BETWEEN 1 AND 18446744073709551615),
  CONSTRAINT ck_cart_item_product_id_range CHECK (product_id BETWEEN 1 AND 18446744073709551615)
);
ALTER SEQUENCE cart_item_id_seq OWNED BY cart_item.id;

CREATE SEQUENCE orders_id_seq AS BIGINT;
CREATE TABLE orders (
  id NUMERIC(20,0) NOT NULL DEFAULT nextval('orders_id_seq'),
  user_id NUMERIC(20,0) NOT NULL,
  checkout_token CHAR(32) COLLATE "C" NOT NULL,
  checkout_request_hash CHAR(64) COLLATE "C" NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  status VARCHAR(12) COLLATE "C" NOT NULL DEFAULT 'PENDING',
  receiver_name VARCHAR(50) COLLATE app_ci NOT NULL,
  receiver_phone VARCHAR(20) COLLATE app_ci NOT NULL,
  receiver_address VARCHAR(255) COLLATE app_ci NOT NULL,
  created_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai'),
  paid_at TIMESTAMP(0) WITHOUT TIME ZONE NULL DEFAULT NULL,
  shipped_at TIMESTAMP(0) WITHOUT TIME ZONE NULL DEFAULT NULL,
  completed_at TIMESTAMP(0) WITHOUT TIME ZONE NULL DEFAULT NULL,
  cancelled_at TIMESTAMP(0) WITHOUT TIME ZONE NULL DEFAULT NULL,
  updated_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai'),
  PRIMARY KEY (id),
  CONSTRAINT uk_orders_user_token UNIQUE (user_id, checkout_token),
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
  ),
  CONSTRAINT ck_orders_id_range CHECK (id BETWEEN 1 AND 18446744073709551615),
  CONSTRAINT ck_orders_user_id_range CHECK (user_id BETWEEN 1 AND 18446744073709551615)
);
ALTER SEQUENCE orders_id_seq OWNED BY orders.id;

CREATE SEQUENCE order_item_id_seq AS BIGINT;
CREATE TABLE order_item (
  id NUMERIC(20,0) NOT NULL DEFAULT nextval('order_item_id_seq'),
  order_id NUMERIC(20,0) NOT NULL,
  product_id NUMERIC(20,0) NOT NULL,
  product_name VARCHAR(100) COLLATE app_ci NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  quantity INT NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT uk_order_item_product UNIQUE (order_id, product_id),
  CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES orders (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_order_item_product FOREIGN KEY (product_id) REFERENCES product (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_order_item_name CHECK (CHAR_LENGTH(TRIM(product_name)) > 0),
  CONSTRAINT ck_order_item_price CHECK (unit_price > 0),
  CONSTRAINT ck_order_item_quantity CHECK (quantity > 0),
  CONSTRAINT ck_order_item_id_range CHECK (id BETWEEN 1 AND 18446744073709551615),
  CONSTRAINT ck_order_item_order_id_range CHECK (order_id BETWEEN 1 AND 18446744073709551615),
  CONSTRAINT ck_order_item_product_id_range CHECK (product_id BETWEEN 1 AND 18446744073709551615)
);
ALTER SEQUENCE order_item_id_seq OWNED BY order_item.id;

CREATE SEQUENCE inventory_id_seq AS BIGINT;
CREATE TABLE inventory (
  id NUMERIC(20,0) NOT NULL DEFAULT nextval('inventory_id_seq'),
  product_id NUMERIC(20,0) NOT NULL,
  available INT NOT NULL DEFAULT 0,
  version NUMERIC(20,0) NOT NULL DEFAULT 0,
  updated_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai'),
  PRIMARY KEY (id),
  CONSTRAINT uk_inventory_product UNIQUE (product_id),
  CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) REFERENCES product (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_inventory_available CHECK (available >= 0),
  CONSTRAINT ck_inventory_id_range CHECK (id BETWEEN 1 AND 18446744073709551615),
  CONSTRAINT ck_inventory_product_id_range CHECK (product_id BETWEEN 1 AND 18446744073709551615),
  CONSTRAINT ck_inventory_version_range CHECK (version BETWEEN 0 AND 18446744073709551615)
);
ALTER SEQUENCE inventory_id_seq OWNED BY inventory.id;

CREATE SEQUENCE payment_id_seq AS BIGINT;
CREATE TABLE payment (
  id NUMERIC(20,0) NOT NULL DEFAULT nextval('payment_id_seq'),
  order_id NUMERIC(20,0) NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  paid_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT uk_payment_order UNIQUE (order_id),
  CONSTRAINT fk_payment_order FOREIGN KEY (order_id) REFERENCES orders (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_payment_amount CHECK (amount > 0),
  CONSTRAINT ck_payment_id_range CHECK (id BETWEEN 1 AND 18446744073709551615),
  CONSTRAINT ck_payment_order_id_range CHECK (order_id BETWEEN 1 AND 18446744073709551615)
);
ALTER SEQUENCE payment_id_seq OWNED BY payment.id;

CREATE INDEX idx_users_role_created ON users (role, created_at, id);
CREATE INDEX idx_product_category_status_price ON product (category_id, status, price, id);
CREATE INDEX idx_product_status_price ON product (status, price, id);
CREATE INDEX idx_cart_item_product ON cart_item (product_id);
CREATE INDEX idx_orders_user_created ON orders (user_id, created_at, id);
CREATE INDEX idx_orders_status_created ON orders (status, created_at, id);
CREATE INDEX idx_orders_created ON orders (created_at, id);
CREATE INDEX idx_order_item_product_order ON order_item (product_id, order_id);
CREATE INDEX idx_payment_paid_order ON payment (paid_at, order_id);
