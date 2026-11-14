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
