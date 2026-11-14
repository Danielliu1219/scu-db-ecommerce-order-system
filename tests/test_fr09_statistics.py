from datetime import datetime, timedelta

from app.database import SessionFactory
from app.models import Order, Payment, User
from app.schemas.payments import Simulate
from app.services import orders, payments, statistics
from sqlalchemy import update

from tests.fixtures import checkout_data


def test_equal_amounts_cross_month_and_boundaries(accounts, goods):
    actor, admin = accounts["alice"], accounts["admin"]
    for when in (
        datetime(2026, 11, 1),
        datetime(2026, 11, 30, 23, 59, 59),
        datetime(2026, 12, 1),
    ):
        order, _ = orders.checkout(actor, checkout_data(actor, goods))
        oid = int(order["order_id"])
        payments.simulate(actor, oid, Simulate(simulate_result="SUCCESS"))
        with SessionFactory.begin() as s:
            s.execute(
                update(Order)
                .where(Order.id == oid)
                .values(created_at=datetime(2026, 10, 31), paid_at=when)
            )
            s.execute(update(Payment).where(Payment.order_id == oid).values(paid_at=when))
    result = statistics.sales(admin, "2026-11-01T00:00:00+08:00", "2026-12-01T00:00:00+08:00")
    assert str(result[0]["sales_amount"]) == "160.00" and result[0]["paid_order_count"] == 2
    top = statistics.sales(admin, "2026-11-01", "2026-12-01", True)
    assert [i["sold_quantity"] for i in top] == [4, 2]


def test_inactive_includes_never_ordered_excludes_cancelled_and_boundary(accounts, goods):
    from app.services.common import now

    actor, admin = accounts["alice"], accounts["admin"]
    order, _ = orders.checkout(actor, checkout_data(actor, goods))
    orders.cancel(actor, int(order["order_id"]))
    with SessionFactory.begin() as s:
        cutoff = now(s)
        s.execute(update(User).values(created_at=cutoff - timedelta(days=40)))
        s.execute(
            update(Order)
            .where(Order.id == int(order["order_id"]))
            .values(created_at=cutoff - timedelta(days=30))
        )
    result = statistics.inactive(admin, cutoff)
    assert [i["username"] for i in result["items"]] == ["bob"]
    with SessionFactory.begin() as s:
        s.execute(
            update(Order)
            .where(Order.id == int(order["order_id"]))
            .values(created_at=cutoff, cancelled_at=cutoff)
        )
    result = statistics.inactive(admin, cutoff)
    assert [i["username"] for i in result["items"]] == ["alice", "bob"]
