from datetime import datetime

import pytest
from app.database import SessionFactory, engine
from app.errors import BusinessError
from app.models import Category, Inventory, Product
from app.schemas.catalog import CategoryInput
from app.schemas.identity import ProfilePatch
from app.services import catalog, identity
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from db.bootstrap import initialize
from tests.fixtures import auth


def test_icu_preserves_case_accent_insensitive_uniqueness_and_literal_search(accounts, goods):
    catalog.save_category(accounts["admin"], CategoryInput(name="Café"))
    with pytest.raises(BusinessError) as duplicate:
        catalog.save_category(accounts["admin"], CategoryInput(name="CAFE"))
    assert duplicate.value.code == "CATEGORY_NAME_EXISTS"
    with SessionFactory.begin() as s:
        product = s.get(Product, int(goods[0]["id"]))
        product.name = "Café_100%"
    for keyword in ("cafe", "CAFÉ", "_100%"):
        result = catalog.products(accounts["alice"], keyword=keyword)
        assert [item["id"] for item in result["items"]] == [goods[0]["id"]]
    assert catalog.products(accounts["alice"], keyword="_200% 止")["total"] == 0


def test_unsigned_64_bit_identifiers_and_versions_stay_exact(client, accounts, goods):
    maximum = 18446744073709551615
    with SessionFactory.begin() as s:
        category_id = s.scalar(select(Category.id).limit(1))
        s.add(
            Product(
                id=maximum,
                category_id=category_id,
                name="大编号商品",
                price="1.00",
                description="精确整数",
                status="ON_SHELF",
            )
        )
        s.flush()
        s.add(Inventory(id=maximum, product_id=maximum, available=1, version=maximum))
    detail = client.get(f"/api/v1/products/{maximum}")
    assert detail.status_code == 200 and detail.json()["data"]["id"] == str(maximum)
    stock = client.get(
        "/api/v1/admin/inventory",
        params={"product_id": str(maximum)},
        headers=auth(accounts["admin"]),
    ).json()["data"]["items"][0]
    assert stock["product_id"] == stock["version"] == str(maximum)
    with pytest.raises(IntegrityError) as overflow:
        with SessionFactory.begin() as s:
            s.execute(
                text("UPDATE inventory SET version=:version WHERE product_id=:id"),
                {"version": maximum + 1, "id": maximum},
            )
    assert overflow.value.orig.sqlstate == "23514"
    with SessionFactory() as s:
        assert s.scalar(select(Inventory.version).where(Inventory.product_id == maximum)) == maximum


def test_profile_updates_timestamp_in_the_business_transaction(accounts):
    with SessionFactory.begin() as s:
        s.execute(
            text("UPDATE users SET updated_at='2000-01-01' WHERE id=:id"),
            {"id": accounts["alice"].id},
        )
    result = identity.profile(accounts["alice"], ProfilePatch(nickname="时间更新"))
    assert result["updated_at"] > datetime(2000, 1, 1)
    assert result["updated_at"].tzinfo is None and result["updated_at"].microsecond == 0


def test_bootstrap_refuses_existing_tables_without_changing_data(accounts, goods):
    with SessionFactory() as s:
        before = s.execute(select(Product.id, Product.name)).all()
    with pytest.raises(ValueError, match="not empty"):
        initialize(engine.url.render_as_string(hide_password=False))
    with SessionFactory() as s:
        assert s.execute(select(Product.id, Product.name)).all() == before
