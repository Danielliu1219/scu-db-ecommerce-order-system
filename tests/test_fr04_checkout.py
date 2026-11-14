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
