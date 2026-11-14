"""Nine ORM mappings generated from the frozen contract DDL. No create_all."""

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, DECIMAL, TINYINT
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    username = Column(String(32), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        String(10, collation="utf8mb4_bin"),
        nullable=False,
        server_default=text("'USER'"),
    )
    nickname = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    __table_args__ = (
        UniqueConstraint("username", name="uk_users_username"),
        Index("idx_users_role_created", "role", "created_at", "id"),
        CheckConstraint("CHAR_LENGTH(TRIM(username)) BETWEEN 3 AND 32", name="ck_users_username"),
        CheckConstraint("CHAR_LENGTH(TRIM(password_hash)) > 0", name="ck_users_password"),
        CheckConstraint("role IN ('USER', 'ADMIN')", name="ck_users_role"),
        CheckConstraint("CHAR_LENGTH(TRIM(nickname)) > 0", name="ck_users_nickname"),
        CheckConstraint("CHAR_LENGTH(TRIM(phone)) > 0", name="ck_users_phone"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )


class Category(Base):
    __tablename__ = "category"
    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    __table_args__ = (
        UniqueConstraint("name", name="uk_category_name"),
        CheckConstraint("CHAR_LENGTH(TRIM(name)) > 0", name="ck_category_name"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )


class Product(Base):
    __tablename__ = "product"
    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    category_id = Column(BIGINT(unsigned=True), nullable=False)
    name = Column(String(100), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(
        String(10, collation="utf8mb4_bin"),
        nullable=False,
        server_default=text("'OFF_SHELF'"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    __table_args__ = (
        Index("idx_product_category_status_price", "category_id", "status", "price", "id"),
        Index("idx_product_status_price", "status", "price", "id"),
        ForeignKeyConstraint(
            ["category_id"],
            ["category.id"],
            name="fk_product_category",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        CheckConstraint("CHAR_LENGTH(TRIM(name)) > 0", name="ck_product_name"),
        CheckConstraint("price > 0", name="ck_product_price"),
        CheckConstraint("status IN ('ON_SHELF', 'OFF_SHELF')", name="ck_product_status"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )


class Cart(Base):
    __tablename__ = "cart"
    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id = Column(BIGINT(unsigned=True), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    __table_args__ = (
        UniqueConstraint("user_id", name="uk_cart_user"),
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_cart_user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )


class CartItem(Base):
    __tablename__ = "cart_item"
    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    cart_id = Column(BIGINT(unsigned=True), nullable=False)
    product_id = Column(BIGINT(unsigned=True), nullable=False)
    quantity = Column(Integer, nullable=False, server_default=text("1"))
    selected = Column(TINYINT, nullable=False, server_default=text("1"))
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uk_cart_item_product"),
        Index("idx_cart_item_product", "product_id"),
        ForeignKeyConstraint(
            ["cart_id"],
            ["cart.id"],
            name="fk_cart_item_cart",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["product_id"],
            ["product.id"],
            name="fk_cart_item_product",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        CheckConstraint("quantity > 0", name="ck_cart_item_quantity"),
        CheckConstraint("selected IN (0, 1)", name="ck_cart_item_selected"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )


class Order(Base):
    __tablename__ = "orders"
    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id = Column(BIGINT(unsigned=True), nullable=False)
    checkout_token = Column(CHAR(32, collation="utf8mb4_bin"), nullable=False)
    checkout_request_hash = Column(CHAR(64, collation="utf8mb4_bin"), nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(
        String(12, collation="utf8mb4_bin"),
        nullable=False,
        server_default=text("'PENDING'"),
    )
    receiver_name = Column(String(50), nullable=False)
    receiver_phone = Column(String(20), nullable=False)
    receiver_address = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    paid_at = Column(DateTime, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    __table_args__ = (
        UniqueConstraint("user_id", "checkout_token", name="uk_orders_user_token"),
        Index("idx_orders_user_created", "user_id", "created_at", "id"),
        Index("idx_orders_status_created", "status", "created_at", "id"),
        Index("idx_orders_created", "created_at", "id"),
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_orders_user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        CheckConstraint("CHAR_LENGTH(checkout_token) = 32", name="ck_orders_token"),
        CheckConstraint("CHAR_LENGTH(checkout_request_hash) = 64", name="ck_orders_hash"),
        CheckConstraint("total_amount > 0", name="ck_orders_total"),
        CheckConstraint(
            "CHAR_LENGTH(TRIM(receiver_name)) > 0 AND CHAR_LENGTH(TRIM(receiver_phone)) > 0 AND CHAR_LENGTH(TRIM(receiver_address)) > 0",
            name="ck_orders_receiver",
        ),
        CheckConstraint(
            "(status = 'PENDING' AND paid_at IS NULL AND shipped_at IS NULL AND completed_at IS NULL AND cancelled_at IS NULL) OR (status = 'PAID' AND paid_at IS NOT NULL AND shipped_at IS NULL AND completed_at IS NULL AND cancelled_at IS NULL) OR (status = 'SHIPPED' AND paid_at IS NOT NULL AND shipped_at IS NOT NULL AND completed_at IS NULL AND cancelled_at IS NULL) OR (status = 'COMPLETED' AND paid_at IS NOT NULL AND shipped_at IS NOT NULL AND completed_at IS NOT NULL AND cancelled_at IS NULL) OR (status = 'CANCELLED' AND paid_at IS NULL AND shipped_at IS NULL AND completed_at IS NULL AND cancelled_at IS NOT NULL)",
            name="ck_orders_status_times",
        ),
        CheckConstraint(
            "(paid_at IS NULL OR paid_at >= created_at) AND (shipped_at IS NULL OR shipped_at >= paid_at) AND (completed_at IS NULL OR completed_at >= shipped_at) AND (cancelled_at IS NULL OR cancelled_at >= created_at)",
            name="ck_orders_time_sequence",
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )


class OrderItem(Base):
    __tablename__ = "order_item"
    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    order_id = Column(BIGINT(unsigned=True), nullable=False)
    product_id = Column(BIGINT(unsigned=True), nullable=False)
    product_name = Column(String(100), nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    __table_args__ = (
        UniqueConstraint("order_id", "product_id", name="uk_order_item_product"),
        Index("idx_order_item_product_order", "product_id", "order_id"),
        ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name="fk_order_item_order",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["product_id"],
            ["product.id"],
            name="fk_order_item_product",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        CheckConstraint("CHAR_LENGTH(TRIM(product_name)) > 0", name="ck_order_item_name"),
        CheckConstraint("unit_price > 0", name="ck_order_item_price"),
        CheckConstraint("quantity > 0", name="ck_order_item_quantity"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    product_id = Column(BIGINT(unsigned=True), nullable=False)
    available = Column(Integer, nullable=False, server_default=text("0"))
    version = Column(BIGINT(unsigned=True), nullable=False, server_default=text("0"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    __table_args__ = (
        UniqueConstraint("product_id", name="uk_inventory_product"),
        ForeignKeyConstraint(
            ["product_id"],
            ["product.id"],
            name="fk_inventory_product",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        CheckConstraint("available >= 0", name="ck_inventory_available"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )


class Payment(Base):
    __tablename__ = "payment"
    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    order_id = Column(BIGINT(unsigned=True), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    paid_at = Column(DateTime, nullable=False)
    __table_args__ = (
        UniqueConstraint("order_id", name="uk_payment_order"),
        Index("idx_payment_paid_order", "paid_at", "order_id"),
        ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name="fk_payment_order",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        CheckConstraint("amount > 0", name="ck_payment_amount"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )
