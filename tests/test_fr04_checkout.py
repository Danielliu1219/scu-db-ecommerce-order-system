from decimal import Decimal

import pytest
from app.checkout_payload import canonical
from app.database import SessionFactory
from app.errors import BusinessError
from app.models import CartItem, Inventory, Order
from app.schemas.catalog import ProductPatch
from app.services import catalog, inventory, orders
from sqlalchemy import func, select

from tests.fixtures import auth, checkout_data


def test_replay_snapshots_and_token_conflict(client, accounts, goods, placed):
    order, data = placed
    assert order["total_amount"] == Decimal("80.00") and len(order["items"]) == 2
    result, status = orders.checkout(accounts["alice"], data)
    assert status == 200 and result["order_id"] == order["order_id"]
    catalog.edit_product(
        accounts["admin"],
        int(goods[0]["id"]),
        ProductPatch(name="新名字", price="40.00"),
    )
    assert (
        orders.detail(accounts["alice"], int(order["order_id"]))["items"][0]["product_name"]
        == "数据线"
    )
    historical = orders.detail(accounts["alice"], int(order["order_id"]))
    assert historical["items"][0]["unit_price"] == Decimal("30.00")
    assert historical["items"][0]["line_amount"] == Decimal("60.00")
    assert historical["total_amount"] == Decimal("80.00")
    changed = data.model_copy(update={"receiver_address": "另一地址"})
    with pytest.raises(BusinessError) as conflict:
        orders.checkout(accounts["alice"], changed)
    assert conflict.value.code == "CHECKOUT_TOKEN_CONFLICT"
    orders.cancel(accounts["alice"], int(order["order_id"]))
    assert orders.checkout(accounts["alice"], data)[0]["status"] == "CANCELLED"
    with SessionFactory() as s:
        assert s.scalar(select(func.count()).select_from(Order)) == 1


def test_partial_failure_rolls_back_everything(monkeypatch, accounts, goods):
    data = checkout_data(accounts["alice"], goods)
    original = inventory.apply_delta
    calls = []

    def failure(s, inv, delta, timestamp):
        calls.append(inv.product_id)
        if len(calls) == 2:
            raise RuntimeError("injected second inventory failure")
        return original(s, inv, delta, timestamp)

    monkeypatch.setattr(inventory, "apply_delta", failure)
    with pytest.raises(RuntimeError):
        orders.checkout(accounts["alice"], data)
    with SessionFactory() as s:
        assert s.scalar(select(func.count()).select_from(Order)) == 0
        assert s.scalar(select(func.count()).select_from(CartItem)) == 2
        assert [
            (i.available, i.version) for i in s.scalars(select(Inventory).order_by(Inventory.id))
        ] == [(20, 1), (20, 1)]
    monkeypatch.setattr(inventory, "apply_delta", original)
    assert orders.checkout(accounts["alice"], data)[1] == 201


def test_cart_changed_and_canonical_payload(client, accounts, goods):
    data = checkout_data(accounts["alice"], goods)
    assert canonical(accounts["alice"].id, data).startswith(b'{"user_id":')
    assert b"\\u" not in canonical(accounts["alice"].id, data)
    payload = data.model_dump(mode="json")
    payload["items"][0]["quantity"] = 1
    r = client.post("/api/v1/orders", headers=auth(accounts["alice"]), json=payload)
    assert r.status_code == 409 and r.json()["error"]["code"] == "CART_CHANGED"
    payload["items"] = []
    assert (
        client.post("/api/v1/orders", headers=auth(accounts["alice"]), json=payload).json()[
            "error"
        ]["code"]
        == "EMPTY_CHECKOUT"
    )
    payload = data.model_dump(mode="json")
    payload["total_amount"] = "0.01"
    assert (
        client.post("/api/v1/orders", headers=auth(accounts["alice"]), json=payload).status_code
        == 422
    )


@pytest.mark.parametrize(
    "case,code",
    [
        ("duplicate", "VALIDATION_ERROR"),
        ("uppercase_token", "VALIDATION_ERROR"),
        ("short_token", "VALIDATION_ERROR"),
        ("nonhex_token", "VALIDATION_ERROR"),
        ("empty", "EMPTY_CHECKOUT"),
        ("int_overflow", "QUANTITY_OVERFLOW"),
    ],
)
def test_invalid_checkout_leaves_cart_and_stock(client, accounts, goods, case, code):
    from app.value_types import INT_MAX

    body = checkout_data(accounts["alice"], goods).model_dump(mode="json")
    if case == "duplicate":
        body["items"].append(dict(body["items"][0]))
    elif case == "empty":
        body["items"] = []
    elif case == "int_overflow":
        body["items"][0]["quantity"] = INT_MAX + 1
    else:
        body["checkout_token"] = {
            "uppercase_token": "A" * 32,
            "short_token": "a" * 31,
            "nonhex_token": "g" * 32,
        }[case]
    r = client.post("/api/v1/orders", headers=auth(accounts["alice"]), json=body)
    assert r.status_code == 422 and r.json()["error"]["code"] == code
    with SessionFactory() as s:
        assert s.scalar(select(func.count()).select_from(Order)) == 0
        assert s.scalar(select(func.count()).select_from(CartItem)) == 2
        assert [(i.available, i.version) for i in s.scalars(select(Inventory))] == [
            (20, 1),
            (20, 1),
        ]


def test_amount_overflow_does_not_consume_token_or_stock(client, accounts, goods):
    data = checkout_data(accounts["alice"], goods)
    pid = int(goods[0]["id"])
    catalog.edit_product(accounts["admin"], pid, ProductPatch(price="99999999.99"))
    r = client.post(
        "/api/v1/orders", headers=auth(accounts["alice"]), json=data.model_dump(mode="json")
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "AMOUNT_OVERFLOW"
    with SessionFactory() as s:
        assert s.scalar(select(func.count()).select_from(Order)) == 0
        assert s.scalar(select(func.count()).select_from(CartItem)) == 2
        assert [(i.available, i.version) for i in s.scalars(select(Inventory))] == [
            (20, 1),
            (20, 1),
        ]
    catalog.edit_product(accounts["admin"], pid, ProductPatch(price="30.00"))
    assert orders.checkout(accounts["alice"], data)[1] == 201


def test_same_token_is_independent_per_user(accounts, goods):
    results = []
    for name in ("alice", "bob"):
        actor = accounts[name]
        data = checkout_data(actor, goods, token_value="a" * 32)
        first, status = orders.checkout(actor, data)
        assert status == 201
        assert orders.checkout(actor, data)[0]["order_id"] == first["order_id"]
        results.append(first)
    assert results[0]["order_id"] != results[1]["order_id"]
    assert results[0]["user_id"] != results[1]["user_id"]
    with SessionFactory() as s:
        assert [(i.available, i.version) for i in s.scalars(select(Inventory))] == [
            (16, 3),
            (18, 3),
        ]


def test_checkout_after_cart_delete_failure_rolls_back(monkeypatch, accounts, goods):
    from app.database import engine
    from app.models import OrderItem
    from sqlalchemy import event

    data = checkout_data(accounts["alice"], goods)

    def reject(conn, cursor, statement, parameters, context, many):
        if statement.startswith("DELETE FROM cart_item"):
            raise RuntimeError("after cart deletion")

    event.listen(engine, "after_cursor_execute", reject)
    try:
        with pytest.raises(RuntimeError):
            orders.checkout(accounts["alice"], data)
    finally:
        event.remove(engine, "after_cursor_execute", reject)
    with SessionFactory() as s:
        assert s.scalar(select(func.count()).select_from(Order)) == 0
        assert s.scalar(select(func.count()).select_from(OrderItem)) == 0
        assert s.scalar(select(func.count()).select_from(CartItem)) == 2
        assert [(i.available, i.version) for i in s.scalars(select(Inventory))] == [
            (20, 1),
            (20, 1),
        ]
    assert orders.checkout(accounts["alice"], data)[1] == 201


def test_replay_uses_normalized_text_ids_and_item_order(client, accounts, goods):
    body = checkout_data(accounts["alice"], goods).model_dump(mode="json")
    body["receiver_name"] = "  e\u0301  "
    first = client.post("/api/v1/orders", headers=auth(accounts["alice"]), json=body)
    assert first.status_code == 201
    body["receiver_name"] = "é"
    body["items"].reverse()
    for item in body["items"]:
        item["cart_item_id"] = "00" + str(item["cart_item_id"])
    replay = client.post("/api/v1/orders", headers=auth(accounts["alice"]), json=body)
    assert replay.status_code == 200 and replay.json() == first.json()
    with SessionFactory() as s:
        assert s.scalar(select(func.count()).select_from(Order)) == 1
        assert [(i.available, i.version) for i in s.scalars(select(Inventory))] == [
            (18, 2),
            (19, 2),
        ]
