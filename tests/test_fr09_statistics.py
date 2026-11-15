from datetime import datetime, timedelta

from app.database import SessionFactory
from app.models import Order, Payment, User
from app.schemas.payments import Simulate
from app.services import orders, payments, statistics
from sqlalchemy import update

from tests.fixtures import checkout_data


def test_top_products_rename_and_ties_take_only_ten(accounts, goods):
    from app.schemas.catalog import ProductCreate, ProductPatch
    from app.schemas.inventory import Restock
    from app.services import catalog, inventory
    from app.services.common import now

    admin, actor = accounts["admin"], accounts["alice"]
    all_goods = list(goods)
    for index in range(10):
        p = catalog.create_product(
            admin,
            ProductCreate(
                category_id=goods[0]["category_id"],
                name=f"tie_{index}",
                price="1.00",
                description="",
                status="ON_SHELF",
            ),
        )
        inventory.maintain(admin, int(p["id"]), Restock(quantity=5, expected_version="0"))
        all_goods.append(p)
    order, _ = orders.checkout(actor, checkout_data(actor, all_goods, (1,) * 12))
    payments.simulate(actor, int(order["order_id"]), Simulate(simulate_result="SUCCESS"))
    catalog.edit_product(admin, int(goods[0]["id"]), ProductPatch(name="renamed"))
    second, _ = orders.checkout(actor, checkout_data(actor, [goods[0]], (1,)))
    payments.simulate(actor, int(second["order_id"]), Simulate(simulate_result="SUCCESS"))
    with SessionFactory() as s:
        cutoff = now(s)
    result = statistics.sales(
        admin, cutoff - timedelta(days=1), cutoff + timedelta(seconds=1), True
    )
    assert len(result) == 10
    assert [int(i["product_id"]) for i in result] == sorted(int(p["id"]) for p in all_goods)[:10]
    assert result[0]["product_name"] == "renamed" and result[0]["sold_quantity"] == 2
    assert [i["sold_quantity"] for i in result[1:]] == [1] * 9
    assert orders.detail(actor, int(order["order_id"]))["items"][0]["product_name"] == "数据线"


def test_inactive_pagination_keeps_original_as_of(monkeypatch, accounts, goods, placed):
    from app.services.common import now
    from app.services.identity import create

    with SessionFactory.begin() as s:
        cutoff = now(s)
        encoded = s.get(User, accounts["alice"].id).password_hash
        for index in range(3):
            u = create(s, f"inactive_{index}", encoded, "test", "test")
            u.created_at = cutoff + timedelta(days=1) if index == 2 else cutoff - timedelta(days=40)
        s.execute(
            update(User)
            .where(User.username.in_(["alice", "bob", "admin"]))
            .values(created_at=cutoff - timedelta(days=40))
        )
        s.execute(update(Order).values(created_at=cutoff - timedelta(days=1)))
    first = statistics.inactive(accounts["admin"], cutoff, page_size=1)
    monkeypatch.setattr(statistics, "now", lambda s: cutoff + timedelta(days=2))
    second = statistics.inactive(accounts["admin"], first["as_of"], page_number=2, page_size=1)
    last = statistics.inactive(accounts["admin"], first["as_of"], page_number=3, page_size=1)
    assert first["as_of"] == second["as_of"] == last["as_of"] == cutoff
    assert first["total"] == second["total"] == last["total"] == 3
    assert [page["items"][0]["username"] for page in (first, second, last)] == [
        "bob",
        "inactive_0",
        "inactive_1",
    ]


def test_statistics_time_errors_are_structured(client, accounts):
    from tests.fixtures import auth

    h = auth(accounts["admin"])
    for route in ("monthly-sales", "top-products"):
        for params in (
            {},
            {"paid_start": "2026-11-01"},
            {"paid_end": "2026-12-01"},
            {"paid_start": "2026-12-01", "paid_end": "2026-11-01"},
            {"paid_start": "0001-01-01T00:00:00+14:00", "paid_end": "2026-11-01"},
        ):
            r = client.get("/api/v1/admin/statistics/" + route, headers=h, params=params)
            assert r.status_code == 422 and r.json()["error"]["code"] == "TIME_RANGE_INVALID"
    for cutoff in ("0001-01-01T00:00:00+14:00", "9999-12-31T23:59:59-14:00", "9999-12-31"):
        r = client.get(
            "/api/v1/admin/statistics/inactive-users", headers=h, params={"as_of": cutoff}
        )
        assert r.status_code == 422 and r.json()["error"]["code"] == "AS_OF_INVALID"


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
