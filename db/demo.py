"""Build all five order states exclusively through the business services."""

import secrets
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / "backend/.env")
from app.database import SessionFactory
from app.dependencies import Principal
from app.models import Inventory, Order, Product, User
from app.schemas.cart import CartAdd
from app.schemas.inventory import Restock
from app.schemas.orders import Checkout
from app.schemas.payments import Simulate
from app.services import cart, inventory, orders, payments
from sqlalchemy import func, select


def demo():
    with SessionFactory() as s:
        if s.scalar(select(func.count()).select_from(Order)):
            raise ValueError(
                "Demo generation requires an empty order set; existing trades were not changed"
            )
        admin_user = s.scalar(select(User).where(User.username == "admin"))
        buyer = s.scalar(select(User).where(User.username == "demo_01"))
        if not admin_user or not buyer:
            raise ValueError("Run db.seed first")
        admin, actor = (
            Principal(admin_user.id, admin_user.role),
            Principal(buyer.id, buyer.role),
        )
        goods = list(
            s.scalars(
                select(Product).where(Product.name.in_(["数据线", "笔记本"])).order_by(Product.id)
            )
        )
        if len(goods) != 2:
            raise ValueError("Expected demo products missing")
        stocks = [(i.product_id, i.available, i.version) for i in s.scalars(select(Inventory))]
    for pid, available, version in stocks:
        if pid in [p.id for p in goods] and available == 0 and version == 0:
            inventory.maintain(admin, pid, Restock(quantity=50, expected_version=version))
    result = []
    for target in ("PENDING", "CANCELLED", "PAID", "SHIPPED", "COMPLETED"):
        items = []
        for p, q in zip(goods, (2, 1)):
            item, _ = cart.add(actor, CartAdd(product_id=p.id, quantity=q))
            items.append({"cart_item_id": item["item"]["id"], "quantity": q})
        order, _ = orders.checkout(
            actor,
            Checkout(
                checkout_token=secrets.token_hex(16),
                items=items,
                receiver_name="演示收件人",
                receiver_phone="演示-000",
                receiver_address="四川大学课程演示地址",
            ),
        )
        oid = int(order["order_id"])
        if target == "CANCELLED":
            orders.cancel(actor, oid)
        elif target != "PENDING":
            payments.simulate(actor, oid, Simulate(simulate_result="SUCCESS"))
            if target in ("SHIPPED", "COMPLETED"):
                orders.advance(admin, oid, True)
            if target == "COMPLETED":
                orders.advance(actor, oid)
        result.append(target)
    return result


if __name__ == "__main__":
    print("Created states: " + ", ".join(demo()))
