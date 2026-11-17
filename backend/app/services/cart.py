from decimal import Decimal

from sqlalchemy import select

from ..dependencies import require
from ..errors import fail, integrity
from ..models import Cart, CartItem, Inventory, Product
from ..transactions import read, write
from ..value_types import INT_MAX
from . import inventory


def container(s, user_id, locked=False):
    stmt = select(Cart).where(Cart.user_id == user_id)
    cart = s.scalar(stmt.with_for_update() if locked else stmt)
    integrity(cart is not None, "普通用户缺少购物车容器")
    return cart


def snapshot(s, user_id):
    cart = container(s, user_id)
    rows = s.execute(
        select(CartItem, Product, Inventory)
        .join(Product, Product.id == CartItem.product_id)
        .outerjoin(Inventory, Inventory.product_id == Product.id)
        .where(CartItem.cart_id == cart.id)
        .order_by(CartItem.id)
    )
    items, total = [], Decimal("0")
    for item, p, inv in rows:
        integrity(inv is not None)
        reason = (
            "PRODUCT_OFF_SHELF"
            if p.status != "ON_SHELF"
            else "STOCK_INSUFFICIENT"
            if item.quantity > inv.available
            else None
        )
        items.append(
            {
                "id": str(item.id),
                "product_id": str(p.id),
                "product_name": p.name,
                "price": p.price,
                "quantity": item.quantity,
                "selected": bool(item.selected),
                "available": inv.available,
                "status": p.status,
                "invalid_reason": reason,
            }
        )
        if item.selected:
            total += p.price * item.quantity
    return {"id": str(cart.id), "items": items, "selected_total": total}


def listing(actor):
    require(actor, "USER")
    return read(lambda s: snapshot(s, actor.id))


def validate_product(s, product_id, quantity):
    p = s.get(Product, product_id, with_for_update=True)
    if p is None:
        fail("PRODUCT_NOT_FOUND", 404)
    inv = inventory.lock(s, product_id)
    if p.status != "ON_SHELF":
        fail("PRODUCT_OFF_SHELF")
    if quantity > inv.available:
        fail("STOCK_INSUFFICIENT")


def add(actor, data):
    require(actor, "USER")

    def change(s):
        c = container(s, actor.id, True)
        item = s.scalar(
            select(CartItem)
            .where(CartItem.cart_id == c.id, CartItem.product_id == data.product_id)
            .with_for_update()
        )
        target = (item.quantity if item else 0) + data.quantity
        if target > INT_MAX:
            fail("QUANTITY_OVERFLOW", 422)
        validate_product(s, data.product_id, target)
        created = item is None
        if created:
            item = CartItem(cart_id=c.id, product_id=data.product_id, quantity=target, selected=1)
            s.add(item)
        else:
            item.quantity = target
        s.flush()
        result = snapshot(s, actor.id)
        return {
            "item": next(i for i in result["items"] if i["id"] == str(item.id)),
            "selected_total": result["selected_total"],
        }, 201 if created else 200

    return write(change)


def edit(actor, item_id, data):
    require(actor, "USER")

    def change(s):
        c = container(s, actor.id, True)
        item = s.scalar(
            select(CartItem)
            .where(CartItem.cart_id == c.id, CartItem.id == item_id)
            .with_for_update()
        )
        if item is None:
            fail("RESOURCE_NOT_FOUND", 404)
        if data.quantity is not None or data.selected is True:
            validate_product(
                s,
                item.product_id,
                data.quantity if data.quantity is not None else item.quantity,
            )
        for key in data.model_fields_set:
            value = getattr(data, key)
            setattr(item, key, int(value) if key == "selected" else value)
        s.flush()
        result = snapshot(s, actor.id)
        return {
            "item": next(i for i in result["items"] if i["id"] == str(item.id)),
            "selected_total": result["selected_total"],
        }

    return write(change)


def remove(actor, item_id):
    require(actor, "USER")

    def change(s):
        c = container(s, actor.id, True)
        item = s.scalar(
            select(CartItem)
            .where(CartItem.cart_id == c.id, CartItem.id == item_id)
            .with_for_update()
        )
        if item is None:
            fail("RESOURCE_NOT_FOUND", 404)
        s.delete(item)
        s.flush()

    write(change)
