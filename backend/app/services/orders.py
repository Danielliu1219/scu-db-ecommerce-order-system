from decimal import Decimal

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from ..checkout_payload import digest
from ..dependencies import require
from ..errors import fail, integrity
from ..models import CartItem, Order, OrderItem, Product
from ..queries import order_filters, order_page, order_snapshots
from ..transactions import constraint_name, read, sqlstate, write
from ..value_types import MAX_MONEY, time_range
from . import cart, inventory
from .common import now, paged


def replay(s, actor, data, request_hash):
    records = order_snapshots(s, user_id=actor.id, token=data.checkout_token)
    if not records:
        return None
    order, old_hash = records[0]
    if old_hash != request_hash:
        fail("CHECKOUT_TOKEN_CONFLICT", 409, "同一结算标识的内容已变化")
    return order, 200


def checkout(actor, data):
    require(actor, "USER")
    request_hash = digest(actor.id, data)

    def change(s):
        c = cart.container(s, actor.id, True)
        old = replay(s, actor, data, request_hash)
        if old is not None:
            return old
        selected = list(
            s.scalars(
                select(CartItem)
                .where(CartItem.cart_id == c.id, CartItem.selected == 1)
                .with_for_update()
            )
        )
        expected = {i.cart_item_id: i.quantity for i in data.items}
        if expected != {i.id: i.quantity for i in selected}:
            fail("CART_CHANGED", 409, "购物车已变化，请重新确认")
        ids = sorted(i.product_id for i in selected)
        products = {pid: s.get(Product, pid, with_for_update=True) for pid in ids}
        stocks = {pid: inventory.lock(s, pid) for pid in ids}
        quantities = {i.product_id: i.quantity for i in selected}
        for pid in ids:
            integrity(products[pid] is not None)
            if products[pid].status != "ON_SHELF":
                fail("PRODUCT_OFF_SHELF")
            if stocks[pid].available < quantities[pid]:
                fail("STOCK_INSUFFICIENT")
        total = sum((products[pid].price * quantities[pid] for pid in ids), Decimal(0))
        if total > MAX_MONEY:
            fail("AMOUNT_OVERFLOW", 422)
        integrity(total > 0 and bool(selected))
        timestamp = now(s)
        order = Order(
            user_id=actor.id,
            checkout_token=data.checkout_token,
            checkout_request_hash=request_hash,
            total_amount=total,
            status="PENDING",
            receiver_name=data.receiver_name,
            receiver_phone=data.receiver_phone,
            receiver_address=data.receiver_address,
            created_at=timestamp,
            updated_at=timestamp,
        )
        s.add(order)
        s.flush()
        for pid in ids:
            p = products[pid]
            s.add(
                OrderItem(
                    order_id=order.id,
                    product_id=pid,
                    product_name=p.name,
                    unit_price=p.price,
                    quantity=quantities[pid],
                )
            )
            s.flush()
            inventory.apply_delta(s, stocks[pid], -quantities[pid], timestamp)
        count = s.execute(
            delete(CartItem)
            .where(CartItem.cart_id == c.id, CartItem.id.in_(list(expected)))
            .execution_options(synchronize_session=False)
        ).rowcount
        integrity(count == len(selected))
        records = order_snapshots(s, user_id=actor.id, ids=[order.id])
        integrity(len(records) == 1)
        return records[0][0], 201

    try:
        return write(change, lambda s: replay(s, actor, data, request_hash))
    except IntegrityError as exc:
        if sqlstate(exc) == "23505" and constraint_name(exc) == "uk_orders_user_token":
            result = read(lambda s: replay(s, actor, data, request_hash))
            integrity(result is not None)
            return result
        raise


def lock_existing(s, actor, order_id, admin=False):
    require(actor, "ADMIN" if admin else "USER")
    order = s.get(Order, order_id, with_for_update=True)
    if order is None or (not admin and order.user_id != actor.id):
        fail("ORDER_NOT_FOUND", 404)
    return order


def snapshot(s, order_id, user_id=None):
    records = order_snapshots(s, user_id=user_id, ids=[order_id])
    if not records:
        fail("ORDER_NOT_FOUND", 404)
    return records[0][0]


def detail(actor, order_id, admin=False):
    require(actor, "ADMIN" if admin else "USER")
    return read(lambda s: snapshot(s, order_id, None if admin else actor.id))


def listing(
    actor,
    admin=False,
    user_id=None,
    order_id=None,
    status=None,
    created_start=None,
    created_end=None,
    page_number=1,
    page_size=20,
):
    require(actor, "ADMIN" if admin else "USER")
    start, end = time_range(created_start, created_end)
    if not admin:
        user_id = actor.id

    def query(s):
        stmt = select(Order.id, Order.created_at).where(*order_filters(user_id, status, start, end))
        if order_id is not None:
            stmt = stmt.where(Order.id == order_id)
        records, total = order_page(s, stmt, page_number, page_size)
        return paged([record[0] for record in records], total, page_number, page_size)

    return read(query)


def resolved_state(s, actor, order_id, states, admin=False):
    order = snapshot(s, order_id, None if admin else actor.id)
    return order if order["status"] in states else None


def cancel(actor, order_id):
    require(actor, "USER")

    def change(s):
        order = lock_existing(s, actor, order_id)
        existing = snapshot(s, order_id, actor.id)
        if order.status == "CANCELLED":
            return existing
        if order.status != "PENDING":
            fail("ORDER_STATE_CONFLICT")
        items = sorted(existing["items"], key=lambda i: int(i["product_id"]))
        stocks = [(inventory.lock(s, int(i["product_id"])), i["quantity"]) for i in items]
        timestamp = now(s, order.created_at)
        for inv, quantity in stocks:
            inventory.apply_delta(s, inv, quantity, timestamp)
        result = s.execute(
            update(Order)
            .where(Order.id == order_id, Order.status == "PENDING")
            .values(status="CANCELLED", cancelled_at=timestamp, updated_at=timestamp)
        )
        integrity(result.rowcount == 1)
        return snapshot(s, order_id, actor.id)

    return write(change, lambda s: resolved_state(s, actor, order_id, ("CANCELLED",)))


def advance(actor, order_id, ship=False):
    require(actor, "ADMIN" if ship else "USER")
    target, expected, field, previous = (
        ("SHIPPED", "PAID", "shipped_at", "paid_at")
        if ship
        else ("COMPLETED", "SHIPPED", "completed_at", "shipped_at")
    )
    repeats = ("SHIPPED", "COMPLETED") if ship else ("COMPLETED",)

    def change(s):
        order = lock_existing(s, actor, order_id, ship)
        existing = snapshot(s, order_id)
        if order.status in repeats:
            return existing
        if order.status != expected:
            fail("ORDER_STATE_CONFLICT")
        timestamp = now(s, getattr(order, previous))
        result = s.execute(
            update(Order)
            .where(Order.id == order_id, Order.status == expected)
            .values(**{"status": target, field: timestamp, "updated_at": timestamp})
        )
        integrity(result.rowcount == 1)
        return snapshot(s, order_id)

    return write(change, lambda s: resolved_state(s, actor, order_id, repeats, ship))
