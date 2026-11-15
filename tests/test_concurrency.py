from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from app.database import SessionFactory
from app.errors import BusinessError
from app.models import CartItem, Inventory, Order, Payment
from app.schemas.inventory import Count
from app.schemas.payments import Simulate
from app.services import inventory, orders, payments
from sqlalchemy import func, select

from tests.fixtures import checkout_data


def race(left, right):
    barrier = Barrier(2)

    def run(operation):
        barrier.wait(timeout=10)
        try:
            return operation()
        except BusinessError as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, op) for op in (left, right)]
        return [f.result(timeout=20) for f in futures]


def test_last_item_one_winner(accounts, goods):
    p = goods[0]
    inventory.maintain(
        accounts["admin"],
        int(p["id"]),
        Count(counted_available=1, expected_version="1"),
        True,
    )
    a = checkout_data(accounts["alice"], [p], (1,))
    b = checkout_data(accounts["bob"], [p], (1,))
    result = race(
        lambda: orders.checkout(accounts["alice"], a),
        lambda: orders.checkout(accounts["bob"], b),
    )
    assert sum(isinstance(r, tuple) for r in result) == 1
    assert [r.code for r in result if isinstance(r, BusinessError)] == ["STOCK_INSUFFICIENT"]
    with SessionFactory() as s:
        assert (
            s.scalar(select(Inventory.available).where(Inventory.product_id == int(p["id"]))) == 0
        )
        assert s.scalar(select(func.count()).select_from(Order)) == 1
        assert s.scalar(select(func.count()).select_from(CartItem)) == 1


def test_same_token_concurrent_only_one_order(accounts, goods):
    actor = accounts["alice"]
    data = checkout_data(actor, goods)
    result = race(lambda: orders.checkout(actor, data), lambda: orders.checkout(actor, data))
    assert sorted(r[1] for r in result) == [200, 201]
    assert result[0][0]["order_id"] == result[1][0]["order_id"]
    with SessionFactory() as s:
        assert [i.available for i in s.scalars(select(Inventory).order_by(Inventory.id))] == [
            18,
            19,
        ]
        assert s.scalar(select(func.count()).select_from(Order)) == 1


def test_payment_and_cancel_have_one_winner(accounts, placed):
    actor = accounts["alice"]
    oid = int(placed[0]["order_id"])
    result = race(
        lambda: orders.cancel(actor, oid),
        lambda: payments.simulate(actor, oid, Simulate(simulate_result="SUCCESS")),
    )
    assert (
        sum(isinstance(r, BusinessError) and r.code == "ORDER_STATE_CONFLICT" for r in result) == 1
    )
    with SessionFactory() as s:
        order = s.get(Order, oid)
        count = s.scalar(select(func.count()).select_from(Payment))
        assert (order.status, count) in [("PAID", 1), ("CANCELLED", 0)]
        assert [i.available for i in s.scalars(select(Inventory).order_by(Inventory.id))] == (
            [18, 19] if count else [20, 20]
        )


def test_stale_inventory_page_after_checkout(accounts, goods, placed):
    with SessionFactory() as s:
        inv = s.scalar(select(Inventory).where(Inventory.product_id == int(goods[0]["id"])))
        assert inv.version == 2
    try:
        inventory.maintain(
            accounts["admin"],
            int(goods[0]["id"]),
            Count(counted_available=20, expected_version="1"),
            True,
        )
    except BusinessError as e:
        assert e.code == "INVENTORY_VERSION_CONFLICT"
    else:
        raise AssertionError("stale version accepted")


def test_count_races_with_checkout_without_lost_stock(accounts, goods):
    p = goods[0]
    actor = accounts["alice"]
    data = checkout_data(actor, [p], (2,))
    results = race(
        lambda: orders.checkout(actor, data),
        lambda: inventory.maintain(
            accounts["admin"],
            int(p["id"]),
            Count(counted_available=19, expected_version="1"),
            True,
        ),
    )
    assert isinstance(results[0], tuple)
    with SessionFactory() as s:
        inv = s.scalar(select(Inventory).where(Inventory.product_id == int(p["id"])))
        assert (inv.available, inv.version) in ((17, 3), (18, 2))
        if isinstance(results[1], BusinessError):
            assert results[1].code == "INVENTORY_VERSION_CONFLICT" and inv.available == 18
        else:
            assert inv.available == 17
