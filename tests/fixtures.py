import pytest
from app.database import SessionFactory
from app.dependencies import Principal
from app.security import hash_password, token
from app.services.identity import create

PASSWORD = "CourseTest2026!"


@pytest.fixture
def accounts():
    with SessionFactory.begin() as s:
        users = {
            name: create(s, name, hash_password(PASSWORD), name, "演示电话", role)
            for name, role in (("alice", "USER"), ("bob", "USER"), ("admin", "ADMIN"))
        }
        result = {name: Principal(u.id, u.role) for name, u in users.items()}
    return result


def auth(actor):
    return {"Authorization": "Bearer " + token(actor.id)}


@pytest.fixture
def goods(accounts):
    from app.schemas.catalog import CategoryInput, ProductCreate
    from app.schemas.inventory import Restock
    from app.services import catalog, inventory

    admin = accounts["admin"]
    c = catalog.save_category(admin, CategoryInput(name="数码"))
    result = []
    for name, price in (("数据线", "30.00"), ("笔记本", "20.00")):
        p = catalog.create_product(
            admin,
            ProductCreate(
                category_id=c["id"],
                name=name,
                price=price,
                description="演示商品",
                status="ON_SHELF",
            ),
        )
        inventory.maintain(admin, int(p["id"]), Restock(quantity=20, expected_version="0"))
        result.append(p)
    return result


def checkout_data(actor, goods, quantities=(2, 1), token_value=None):
    import secrets

    from app.schemas.cart import CartAdd
    from app.schemas.orders import Checkout
    from app.services import cart

    items = []
    for p, q in zip(goods, quantities):
        result, _ = cart.add(actor, CartAdd(product_id=p["id"], quantity=q))
        items.append({"cart_item_id": result["item"]["id"], "quantity": q})
    return Checkout(
        checkout_token=token_value or secrets.token_hex(16),
        items=items,
        receiver_name="演示收件人",
        receiver_phone="00123",
        receiver_address="四川大学 演示地址",
    )


@pytest.fixture
def placed(accounts, goods):
    from app.services.orders import checkout

    data = checkout_data(accounts["alice"], goods)
    order, _ = checkout(accounts["alice"], data)
    return order, data
