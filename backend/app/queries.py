from decimal import Decimal
from pathlib import Path

from sqlalchemy import bindparam, text

from .errors import integrity

DIRECTORY = Path(__file__).resolve().parents[2] / "db/queries"
NAMES = {
    1: "q1_orders",
    2: "q2_monthly_sales",
    3: "q3_top_products",
    4: "q4_inactive_users",
}


def sql(number):
    return (DIRECTORY / (NAMES[number] + ".sql")).read_text(encoding="utf-8").strip().rstrip(";")


def order_snapshots(s, user_id=None, status=None, start_at=None, end_at=None, ids=None, token=None):
    # The same SELECT supplies header, details and payment at READ COMMITTED.
    query = sql(1).replace(
        "SELECT o.id AS order_id", "SELECT o.checkout_request_hash, o.id AS order_id"
    )
    query = query.replace("JOIN order_item AS oi", "LEFT JOIN order_item AS oi")
    query = query.replace(
        "o.created_at >= :start_at", "(:start_at IS NULL OR o.created_at >= :start_at)"
    )
    query = query.replace("o.created_at < :end_at", "(:end_at IS NULL OR o.created_at < :end_at)")
    params = dict(user_id=user_id, status=status, start_at=start_at, end_at=end_at)
    clauses = []
    if ids is not None:
        if not ids:
            return []
        clauses.append("o.id IN :ids")
        params["ids"] = ids
    if token is not None:
        clauses.append("o.checkout_token = :token")
        params["token"] = token
    if clauses:
        query = query.replace("ORDER BY", "AND " + " AND ".join(clauses) + "\nORDER BY")
    statement = text(query)
    if ids is not None:
        statement = statement.bindparams(bindparam("ids", expanding=True))
    grouped = {}
    for row in s.execute(statement, params).mappings():
        oid = row["order_id"]
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
