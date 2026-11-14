from sqlalchemy import func, select, update

from ..dependencies import require
from ..errors import fail, integrity
from ..models import Inventory, Order, OrderItem, Product
from ..transactions import read, write
from ..value_types import INT_MAX, json_value
from .common import contains, now, page, paged


def lock(s, product_id):
    inv = s.scalar(select(Inventory).where(Inventory.product_id == product_id).with_for_update())
    integrity(inv is not None, "商品缺少库存记录")
    return inv


def apply_delta(s, inv, delta, timestamp):
    target = inv.available + delta
    if target > INT_MAX:
        fail("QUANTITY_OVERFLOW", 422)
    if target < 0:
        fail("STOCK_INSUFFICIENT", 409, "可售库存不足")
    result = s.execute(
        update(Inventory)
        .where(
            Inventory.product_id == inv.product_id,
            Inventory.version == inv.version,
            Inventory.available + delta >= 0,
        )
        .values(
            available=Inventory.available + delta,
            version=Inventory.version + 1,
            updated_at=timestamp,
        )
        .execution_options(synchronize_session=False)
    )
    integrity(result.rowcount == 1)
    s.refresh(inv)


def mutation(inv, delta):
    return {
        "product_id": str(inv.product_id),
        "available": inv.available,
        "version": str(inv.version),
        "updated_at": inv.updated_at,
        "delta": delta,
    }


def listing(actor, product_id=None, keyword=None, page_number=1, page_size=20):
    require(actor, "ADMIN")

    def query(s):
        occupied = (
            select(OrderItem.product_id, func.sum(OrderItem.quantity).label("quantity"))
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status == "PENDING")
            .group_by(OrderItem.product_id)
            .subquery()
        )
        stmt = (
            select(Inventory, Product.name, func.coalesce(occupied.c.quantity, 0))
            .join(Product, Product.id == Inventory.product_id)
            .outerjoin(occupied, occupied.c.product_id == Inventory.product_id)
            .order_by(Inventory.id)
        )
        if product_id is not None:
            stmt = stmt.where(Product.id == product_id)
        if keyword:
            stmt = stmt.where(contains(Product.name, keyword))
        rows, total = page(s, stmt, page_number, page_size)
        items = [
            {
                "id": str(i.id),
                "product_id": str(i.product_id),
                "product_name": name,
                "available": i.available,
                "version": str(i.version),
                "pending_occupied": int(occupied),
                "updated_at": i.updated_at,
            }
            for i, name, occupied in rows
        ]
        return paged(items, total, page_number, page_size)

    return read(query)


def maintain(actor, product_id, data, count=False):
    require(actor, "ADMIN")

    def change(s):
        if not s.get(Product, product_id, with_for_update=True):
            fail("PRODUCT_NOT_FOUND", 404)
        inv = lock(s, product_id)
        if inv.version != data.expected_version:
            details = mutation(inv, 0)
            details.pop("delta")
            fail(
                "INVENTORY_VERSION_CONFLICT",
                409,
                "库存已变化，请刷新后重新确认",
                json_value(details),
            )
        delta = data.counted_available - inv.available if count else data.quantity
        apply_delta(s, inv, delta, now(s))
        return mutation(inv, delta)

    return write(change)
