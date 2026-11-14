from app.database import SessionFactory
from app.models import Inventory
from app.schemas.payments import Simulate
from app.services import orders, payments
from sqlalchemy import select

from tests.fixtures import auth, checkout_data


def test_cancel_is_once_and_permissions(client, accounts, goods, placed):
    order, _ = placed
    oid = order["order_id"]
    h = auth(accounts["alice"])
    assert client.get("/api/v1/orders/" + oid, headers=auth(accounts["bob"])).status_code == 404
    assert (
        client.post(
            "/api/v1/orders/" + oid + "/cancel", headers=auth(accounts["admin"])
        ).status_code
        == 403
    )
    first = client.post("/api/v1/orders/" + oid + "/cancel", headers=h)
    assert first.status_code == 200 and first.json()["data"]["status"] == "CANCELLED"
    assert (
        client.post("/api/v1/orders/" + oid + "/cancel", headers=h).json()["data"]["cancelled_at"]
        == first.json()["data"]["cancelled_at"]
    )
    with SessionFactory() as s:
        assert [i.available for i in s.scalars(select(Inventory).order_by(Inventory.id))] == [
            20,
            20,
        ]


def test_state_machine_and_order_pagination(client, accounts, goods, placed):
    order, _ = placed
    oid = int(order["order_id"])
    actor = accounts["alice"]
    admin = accounts["admin"]
    assert client.post(f"/api/v1/admin/orders/{oid}/ship", headers=auth(admin)).status_code == 409
    payments.simulate(actor, oid, Simulate(simulate_result="SUCCESS"))
    shipped = orders.advance(admin, oid, True)
    complete = orders.advance(actor, oid)
    assert (
        complete["created_at"]
        <= complete["paid_at"]
        <= complete["shipped_at"]
        <= complete["completed_at"]
    )
    assert orders.advance(admin, oid, True)["shipped_at"] == shipped["shipped_at"]
    assert orders.advance(actor, oid)["completed_at"] == complete["completed_at"]
    assert client.post(f"/api/v1/orders/{oid}/cancel", headers=auth(actor)).status_code == 409
    orders.checkout(actor, checkout_data(actor, goods))
    listing = client.get("/api/v1/orders?page_size=1", headers=auth(actor)).json()["data"]
    assert (
        listing["total"] == 2
        and len(listing["items"]) == 1
        and len(listing["items"][0]["items"]) == 2
    )


def test_cancel_second_item_overflow_rolls_back_first(accounts, goods, placed):
    import pytest
    from app.errors import BusinessError
    from app.schemas.inventory import Count
    from app.services import inventory
    from app.value_types import INT_MAX

    oid = int(placed[0]["order_id"])
    inventory.maintain(
        accounts["admin"],
        int(goods[1]["id"]),
        Count(counted_available=INT_MAX, expected_version="2"),
        True,
    )
    with pytest.raises(BusinessError) as error:
        orders.cancel(accounts["alice"], oid)
    assert error.value.code == "QUANTITY_OVERFLOW"
    with SessionFactory() as s:
        assert [i.available for i in s.scalars(select(Inventory).order_by(Inventory.id))] == [
            18,
            INT_MAX,
        ]
    assert orders.detail(accounts["alice"], oid)["status"] == "PENDING"
