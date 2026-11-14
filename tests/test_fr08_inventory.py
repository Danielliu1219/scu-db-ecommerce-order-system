from app.database import SessionFactory
from app.models import Inventory
from app.value_types import INT_MAX
from sqlalchemy import select

from tests.fixtures import auth


def test_version_count_and_overflow(client, accounts, goods):
    p = goods[0]["id"]
    path = f"/api/v1/admin/inventory/{p}"
    h = auth(accounts["admin"])
    r = client.post(
        path + "/count",
        headers=h,
        json={"counted_available": 20, "expected_version": "1"},
    )
    assert (
        r.status_code == 200
        and r.json()["data"]["version"] == "2"
        and r.json()["data"]["delta"] == 0
    )
    conflict = client.post(
        path + "/restock", headers=h, json={"quantity": 2, "expected_version": "1"}
    )
    assert conflict.status_code == 409 and conflict.json()["error"]["details"]["version"] == "2"
    r = client.post(
        path + "/count",
        headers=h,
        json={"counted_available": INT_MAX, "expected_version": "2"},
    )
    assert r.status_code == 200
    assert (
        client.post(
            path + "/restock", headers=h, json={"quantity": 1, "expected_version": "3"}
        ).json()["error"]["code"]
        == "QUANTITY_OVERFLOW"
    )
    with SessionFactory() as s:
        inv = s.scalar(select(Inventory).where(Inventory.product_id == int(p)))
        assert inv.available == INT_MAX and inv.version == 3
    assert (
        client.post(
            path + "/restock",
            headers=auth(accounts["alice"]),
            json={"quantity": 1, "expected_version": "3"},
        ).status_code
        == 403
    )
