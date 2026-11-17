"""Nine ORM mappings matching the PostgreSQL contract DDL. No create_all."""

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    Sequence,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator


class UInt64(TypeDecorator):
    """Exact unsigned identifier/version range without float conversion."""

    impl = Numeric(20, 0)
    cache_ok = True

    def process_result_value(self, value, dialect):
        return int(value) if value is not None else None


def primary_key(table):
    sequence = Sequence(f"{table}_id_seq")
    return Column(
        UInt64(),
        sequence,
        server_default=sequence.next_value(),
        primary_key=True,
        autoincrement=False,
    )


LOCAL_NOW = "date_trunc('second', statement_timestamp() AT TIME ZONE 'Asia/Shanghai')"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = primary_key("users")
    username = Column(String(32, collation="app_ci"), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        String(10, collation="C"),
        nullable=False,
        server_default=text("'USER'"),
    )
    nickname = Column(String(50, collation="app_ci"), nullable=False)
    phone = Column(String(20, collation="app_ci"), nullable=False)
    created_at = Column(TIMESTAMP(precision=0), nullable=False, server_default=text(LOCAL_NOW))
    updated_at = Column(
        TIMESTAMP(precision=0),
        nullable=False,
        server_default=text(LOCAL_NOW),
        onupdate=text(LOCAL_NOW),
    )
    __table_args__ = (
        UniqueConstraint("username", name="uk_users_username"),
        Index("idx_users_role_created", "role", "created_at", "id"),
        CheckConstraint("CHAR_LENGTH(TRIM(username)) BETWEEN 3 AND 32", name="ck_users_username"),
        CheckConstraint("CHAR_LENGTH(TRIM(password_hash)) > 0", name="ck_users_password"),
        CheckConstraint("role IN ('USER', 'ADMIN')", name="ck_users_role"),
        CheckConstraint("CHAR_LENGTH(TRIM(nickname)) > 0", name="ck_users_nickname"),
        CheckConstraint("CHAR_LENGTH(TRIM(phone)) > 0", name="ck_users_phone"),
    )


class Category(Base):
    __tablename__ = "category"
    id = primary_key("category")
    name = Column(String(50, collation="app_ci"), nullable=False)
    created_at = Column(TIMESTAMP(precision=0), nullable=False, server_default=text(LOCAL_NOW))
    updated_at = Column(
        TIMESTAMP(precision=0),
        nullable=False,
        server_default=text(LOCAL_NOW),
        onupdate=text(LOCAL_NOW),
    )
    __table_args__ = (
        UniqueConstraint("name", name="uk_category_name"),
        CheckConstraint("CHAR_LENGTH(TRIM(name)) > 0", name="ck_category_name"),
    )


class Product(Base):
    __tablename__ = "product"
    id = primary_key("product")
    category_id = Column(UInt64(), nullable=False)
    name = Column(String(100, collation="app_ci"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    description = Column(Text(collation="app_ci"), nullable=False)
    status = Column(
        String(10, collation="C"),
        nullable=False,
        server_default=text("'OFF_SHELF'"),
    )
    created_at = Column(TIMESTAMP(precision=0), nullable=False, server_default=text(LOCAL_NOW))
    updated_at = Column(
        TIMESTAMP(precision=0),
        nullable=False,
        server_default=text(LOCAL_NOW),
        onupdate=text(LOCAL_NOW),
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
    )


class Cart(Base):
    __tablename__ = "cart"
    id = primary_key("cart")
    user_id = Column(UInt64(), nullable=False)
    created_at = Column(TIMESTAMP(precision=0), nullable=False, server_default=text(LOCAL_NOW))
    __table_args__ = (
        UniqueConstraint("user_id", name="uk_cart_user"),
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_cart_user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
    )


class CartItem(Base):
    __tablename__ = "cart_item"
    id = primary_key("cart_item")
    cart_id = Column(UInt64(), nullable=False)
    product_id = Column(UInt64(), nullable=False)
    quantity = Column(Integer, nullable=False, server_default=text("1"))
    selected = Column(SmallInteger, nullable=False, server_default=text("1"))
    created_at = Column(TIMESTAMP(precision=0), nullable=False, server_default=text(LOCAL_NOW))
    updated_at = Column(
        TIMESTAMP(precision=0),
        nullable=False,
        server_default=text(LOCAL_NOW),
        onupdate=text(LOCAL_NOW),
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
    )


class Order(Base):
    __tablename__ = "orders"
    id = primary_key("orders")
    user_id = Column(UInt64(), nullable=False)
    checkout_token = Column(CHAR(32, collation="C"), nullable=False)
    checkout_request_hash = Column(CHAR(64, collation="C"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(
        String(12, collation="C"),
        nullable=False,
        server_default=text("'PENDING'"),
    )
    receiver_name = Column(String(50, collation="app_ci"), nullable=False)
    receiver_phone = Column(String(20, collation="app_ci"), nullable=False)
    receiver_address = Column(String(255, collation="app_ci"), nullable=False)
    created_at = Column(TIMESTAMP(precision=0), nullable=False, server_default=text(LOCAL_NOW))
    paid_at = Column(TIMESTAMP(precision=0), nullable=True)
    shipped_at = Column(TIMESTAMP(precision=0), nullable=True)
    completed_at = Column(TIMESTAMP(precision=0), nullable=True)
    cancelled_at = Column(TIMESTAMP(precision=0), nullable=True)
    updated_at = Column(
        TIMESTAMP(precision=0),
        nullable=False,
        server_default=text(LOCAL_NOW),
        onupdate=text(LOCAL_NOW),
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
    )


class OrderItem(Base):
    __tablename__ = "order_item"
    id = primary_key("order_item")
    order_id = Column(UInt64(), nullable=False)
    product_id = Column(UInt64(), nullable=False)
    product_name = Column(String(100, collation="app_ci"), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
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
    )


class Inventory(Base):
    __tablename__ = "inventory"
    id = primary_key("inventory")
    product_id = Column(UInt64(), nullable=False)
    available = Column(Integer, nullable=False, server_default=text("0"))
    version = Column(UInt64(), nullable=False, server_default=text("0"))
    updated_at = Column(
        TIMESTAMP(precision=0),
        nullable=False,
        server_default=text(LOCAL_NOW),
        onupdate=text(LOCAL_NOW),
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
    )


class Payment(Base):
    __tablename__ = "payment"
    id = primary_key("payment")
    order_id = Column(UInt64(), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    paid_at = Column(TIMESTAMP(precision=0), nullable=False)
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
    )


for table in Base.metadata.tables.values():
    for column in table.columns:
        if isinstance(column.type, UInt64):
            minimum = 0 if column.name == "version" else 1
            table.append_constraint(
                CheckConstraint(
                    f"{column.name} BETWEEN {minimum} AND 18446744073709551615",
                    name=f"ck_{table.name}_{column.name}_range",
                )
            )
