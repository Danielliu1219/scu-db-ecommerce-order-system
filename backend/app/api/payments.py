from fastapi import APIRouter

from ..dependencies import Actor
from ..schemas.common import Response
from ..schemas.payments import PaymentQuery, Simulate, SimulateOut
from ..services import payments
from ..value_types import ID
from .common import response

router = APIRouter(tags=["FR-06 模拟支付"])


@router.post(
    "/orders/{order_id}/payments/simulate",
    response_model=Response[SimulateOut],
    responses={201: {"model": Response[SimulateOut]}},
)
def simulate(actor: Actor, order_id: ID, data: Simulate):
    result, status = payments.simulate(actor, order_id, data)
    return response(result, status)


@router.get("/orders/{order_id}/payment", response_model=Response[PaymentQuery])
def payment(actor: Actor, order_id: ID):
    return response(payments.payment(actor, order_id))


@router.get("/admin/payments", response_model=Response[PaymentQuery])
def admin_payment(actor: Actor, order_id: ID):
    return response(payments.payment(actor, order_id, True))
