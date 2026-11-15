from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select, true

from .errors import integrity
from .models import Order, OrderItem, Payment, User

DIRECTORY = Path(__file__).resolve().parents[2] / "db/queries"
NAMES = {
    1: "q1_orders",
    2: "q2_monthly_sales",
    3: "q3_top_products",
    4: "q4_inactive_users",
}


def sql(number):
    return (DIRECTORY / (NAMES[number] + ".sql")).read_text(encoding="utf-8").strip().rstrip(";")


def page_parts(statement, page_number, page_size, order_columns=("id",), descending=False):
    """Count and limit the same filtered IDs inside one SELECT, including empty pages."""
    filtered = statement.order_by(None).cte("filtered_ids")
    ordering = [filtered.c[name] for name in order_columns]
    if descending:
        ordering = [column.desc() for column in ordering]
    page_rows = (
        select(filtered)
        .order_by(*ordering)
        .offset((page_number - 1) * page_size)
        .limit(page_size)
        .subquery("page_rows")
    )
    totals = select(func.count().label("total")).select_from(filtered).subquery("page_total")
    return page_rows, totals


def order_filters(user_id=None, status=None, start_at=None, end_at=None, ids=None, token=None):
    clauses = []
    if user_id is not None:
        clauses.append(Order.user_id == user_id)
    if status is not None:
        clauses.append(Order.status == status)
    if start_at is not None:
        clauses.append(Order.created_at >= start_at)
    if end_at is not None:
        clauses.append(Order.created_at < end_at)
    if ids is not None:
        clauses.append(Order.id.in_(ids))
    if token is not None:
        clauses.append(Order.checkout_token == token)
    return clauses


def order_statement():
    # Independent application query; q1_orders.sql remains the teaching contract query.
    return (
        select(
            Order.checkout_request_hash,
            Order.id.label("order_id"),
            Order.user_id,
            User.username,
            Order.status,
            Order.created_at,
            Order.total_amount,
            Order.receiver_name,
            Order.receiver_phone,
            Order.receiver_address,
            Order.paid_at,
            Order.shipped_at,
            Order.completed_at,
            Order.cancelled_at,
            OrderItem.id.label("order_item_id"),
            OrderItem.product_id,
            OrderItem.product_name,
            OrderItem.unit_price,
            OrderItem.quantity,
            (OrderItem.unit_price * OrderItem.quantity).label("line_amount"),
            Payment.id.label("payment_id"),
            Payment.amount.label("payment_amount"),
            Payment.paid_at.label("payment_time"),
        )
        .select_from(Order)
        .join(User, User.id == Order.user_id)
        .outerjoin(OrderItem, OrderItem.order_id == Order.id)
        .outerjoin(Payment, Payment.order_id == Order.id)
    )


def order_snapshots(s, user_id=None, status=None, start_at=None, end_at=None, ids=None, token=None):
    if ids is not None and not ids:
        return []
    statement = (
        order_statement()
        .where(*order_filters(user_id, status, start_at, end_at, ids, token))
        .order_by(Order.created_at.desc(), Order.id.desc(), OrderItem.id)
    )
    return assemble_orders(s.execute(statement).mappings())


def order_page(s, filtered, page_number, page_size):
    page_rows, totals = page_parts(
        filtered, page_number, page_size, ("created_at", "id"), descending=True
    )
    details = (
        order_statement().join(page_rows, page_rows.c.id == Order.id).subquery("order_details")
    )
    statement = (
        select(totals.c.total, details)
        .select_from(totals.outerjoin(details, true()))
        .order_by(details.c.created_at.desc(), details.c.order_id.desc(), details.c.order_item_id)
    )
    rows = s.execute(statement).mappings().all()
    return assemble_orders(rows), rows[0]["total"]


def assemble_orders(rows):
    grouped = {}
    for row in rows:
        oid = row["order_id"]
        if oid is None:  # Total-only row for an empty or out-of-range page.
            continue
        if oid not in grouped:
            fields = (
                "username",
                "status",
                "created_at",
                "total_amount",
                "receiver_name",
                "receiver_phone",
                "receiver_address",
                "paid_at",
                "shipped_at",
                "completed_at",
                "cancelled_at",
            )
            order = {key: row[key] for key in fields}
            order.update(order_id=str(oid), user_id=str(row["user_id"]), items=[], payment=None)
            if row["payment_id"] is not None:
                order["payment"] = {
                    "payment_id": str(row["payment_id"]),
                    "amount": row["payment_amount"],
                    "paid_at": row["payment_time"],
                }
            grouped[oid] = order, row["checkout_request_hash"]
        order = grouped[oid][0]
        integrity(row["order_item_id"] is not None, "订单缺少明细")
        order["items"].append(
            {
                "id": str(row["order_item_id"]),
                "product_id": str(row["product_id"]),
                "product_name": row["product_name"],
                "unit_price": row["unit_price"],
                "quantity": row["quantity"],
                "line_amount": row["line_amount"],
            }
        )
    for order, _ in grouped.values():
        integrity(
            sum((i["unit_price"] * i["quantity"] for i in order["items"]), Decimal(0))
            == order["total_amount"]
        )
        paid = order["status"] in ("PAID", "SHIPPED", "COMPLETED")
        payment = order["payment"]
        integrity((payment is not None) == paid)
        if paid:
            integrity(
                payment["amount"] == order["total_amount"]
                and payment["paid_at"] == order["paid_at"]
            )
    return list(grouped.values())
