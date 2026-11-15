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
    details = conflict.json()["error"]["details"]
    assert set(details) == {"product_id", "available", "version", "updated_at"}
    assert details["product_id"] == p and details["available"] == 20
    assert details["updated_at"].endswith("+08:00")
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


def test_count_positive_negative_and_zero_deltas(client, accounts, goods):
    p = goods[0]["id"]
    path = f"/api/v1/admin/inventory/{p}/count"
    h = auth(accounts["admin"])
    for target, version, delta in [(17, 1, -3), (22, 2, 5), (22, 3, 0)]:
        r = client.post(
            path, headers=h, json={"counted_available": target, "expected_version": str(version)}
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert (data["available"], data["delta"], data["version"]) == (
            target,
            delta,
            str(version + 1),
        )
    for target in [-1, INT_MAX + 1]:
        r = client.post(
            path, headers=h, json={"counted_available": target, "expected_version": "4"}
        )
        assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    with SessionFactory() as s:
        inv = s.scalar(select(Inventory).where(Inventory.product_id == int(p)))
        assert (inv.available, inv.version) == (22, 4)
