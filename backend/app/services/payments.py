from sqlalchemy import update

from ..dependencies import require
from ..errors import fail, integrity
from ..models import Order, Payment
from ..transactions import read, write
from . import orders
from .common import now


def query_result(order):
    return {"payment": order["payment"], "order_status": order["status"]}


def success(order):
    return {**query_result(order), "result": "SUCCESS", **order["payment"]}


def simulate(actor, order_id, data):
    require(actor, "USER")

    def change(s):
        order = orders.lock_existing(s, actor, order_id)
        existing = orders.snapshot(s, order_id, actor.id)
        if order.status in ("PAID", "SHIPPED", "COMPLETED"):
            return success(existing), 200
        if order.status != "PENDING":
            fail("ORDER_STATE_CONFLICT")
        if data.simulate_result == "FAILURE":
            return {
                "result": "FAILURE",
                "payment": None,
                "order_status": "PENDING",
            }, 200
        timestamp = now(s, order.created_at)
        s.add(Payment(order_id=order.id, amount=order.total_amount, paid_at=timestamp))
        s.flush()
        result = s.execute(
            update(Order)
            .where(Order.id == order_id, Order.status == "PENDING")
            .values(status="PAID", paid_at=timestamp, updated_at=timestamp)
        )
        integrity(result.rowcount == 1)
        return success(orders.snapshot(s, order_id, actor.id)), 201

    def resolve(s):
        order = orders.snapshot(s, order_id, actor.id)
        return (success(order), 200) if order["payment"] else None

    return write(change, resolve)


def payment(actor, order_id, admin=False):
    require(actor, "ADMIN" if admin else "USER")
    return read(lambda s: query_result(orders.snapshot(s, order_id, None if admin else actor.id)))
