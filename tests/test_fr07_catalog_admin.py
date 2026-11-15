import pytest
from app.database import SessionFactory
from app.models import Inventory, Product
from app.schemas.catalog import ProductCreate
from app.services import catalog
from sqlalchemy import select

from tests.fixtures import auth

BASE = "/api/v1/admin"


def test_crud_and_delete_protection(client, accounts):
    h = auth(accounts["admin"])
    c = client.post(BASE + "/categories", headers=h, json={"name": " 文具 "}).json()["data"]
    assert client.post(BASE + "/categories", headers=h, json={"name": "文具"}).status_code == 409
    body = {"category_id": c["id"], "name": "本子", "price": "20.00", "description": ""}
    r = client.post(BASE + "/products", headers=h, json=body)
    assert r.status_code == 201, r.text
    p = r.json()["data"]
    assert p["available"] == 0 and p["status"] == "OFF_SHELF"
    assert (
        client.delete(BASE + "/categories/" + c["id"], headers=h).json()["error"]["code"]
        == "CATEGORY_IN_USE"
    )
    assert (
        client.put(
            BASE + "/products/" + p["id"] + "/status",
            headers=h,
            json={"status": "ON_SHELF"},
        ).status_code
        == 200
    )
    assert client.delete(BASE + "/products/" + p["id"], headers=h).status_code == 204
    assert client.delete(BASE + "/categories/" + c["id"], headers=h).status_code == 204


@pytest.mark.parametrize("price", ["0", "1.001", "100000000.00", "NaN"])
def test_invalid_price(client, accounts, price):
    h = auth(accounts["admin"])
    r = client.post(
        BASE + "/products",
        headers=h,
        json={"category_id": "1", "name": "p", "price": price, "description": ""},
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "PRICE_INVALID"


def test_inventory_insert_failure_rolls_back_product(accounts, goods):
    from sqlalchemy import event

    def reject(*args):
        raise RuntimeError("injected inventory failure")

    event.listen(Inventory, "before_insert", reject)
    try:
        with pytest.raises(RuntimeError):
            catalog.create_product(
                accounts["admin"],
                ProductCreate(
                    category_id=goods[0]["category_id"],
                    name="回滚商品",
                    price="1.00",
                    description="",
                ),
            )
    finally:
        event.remove(Inventory, "before_insert", reject)
    with SessionFactory() as s:
        assert s.scalar(select(Product).where(Product.name == "回滚商品")) is None


def test_nonzero_inventory_blocks_product_deletion(client, accounts, goods):
    pid = goods[0]["id"]
    r = client.delete(BASE + "/products/" + pid, headers=auth(accounts["admin"]))
    assert r.status_code == 409 and r.json()["error"]["code"] == "INVENTORY_NOT_ZERO"
    with SessionFactory() as s:
        assert s.get(Product, int(pid)) is not None
        inv = s.scalar(select(Inventory).where(Inventory.product_id == int(pid)))
        assert (inv.available, inv.version) == (20, 1)


def test_historical_order_reference_blocks_zero_stock_deletion(client, accounts, goods, placed):
    from app.schemas.inventory import Count
    from app.services import inventory, orders

    orders.cancel(accounts["alice"], int(placed[0]["order_id"]))
    pid = goods[0]["id"]
    inventory.maintain(
        accounts["admin"], int(pid), Count(counted_available=0, expected_version="3"), True
    )
    r = client.delete(BASE + "/products/" + pid, headers=auth(accounts["admin"]))
    assert r.status_code == 409 and r.json()["error"]["code"] == "PRODUCT_IN_USE"
    with SessionFactory() as s:
        assert s.get(Product, int(pid)) is not None
        inv = s.scalar(select(Inventory).where(Inventory.product_id == int(pid)))
        assert (inv.available, inv.version) == (0, 4)
