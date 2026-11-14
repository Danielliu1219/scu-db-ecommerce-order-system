from typing import Literal

from pydantic import BaseModel

from ..value_types import OrderStatus
from .common import Input
from .orders import PaymentOut


class Simulate(Input):
    simulate_result: Literal["SUCCESS", "FAILURE"]


class PaymentQuery(BaseModel):
    payment: PaymentOut | None
    order_status: OrderStatus


class SimulateOut(PaymentQuery):
    result: Literal["SUCCESS", "FAILURE"]
    payment_id: str | None = None
    amount: str | None = None
    paid_at: str | None = None
